"""
FAQ Cache Service.

Two-tier caching for frequently asked questions:
  1. Exact-match cache: O(1) lookup on normalized query
  2. Semantic cache: Embedding-based similarity for paraphrases

When the same (or similar) question is asked again, return the cached
response instantly instead of running the full RAG + LLM pipeline.

Tracks hit counts to surface "trending" FAQs.
Persists to disk so warmed cache survives restarts.
"""
import json
import re
import threading
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

from app.services.logger import get_logger

logger = get_logger("faq_cache")

CACHE_FILE = Path(__file__).parent.parent.parent / "data" / "faq_cache.json"
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

# Tunables
MAX_CACHE_SIZE = 200          # max number of cached Q/A pairs
SIMILARITY_THRESHOLD = 0.88   # cosine similarity required to count as a hit
CACHE_TTL_HOURS = 24 * 7      # entries expire after 7 days unless re-hit
MIN_QUESTION_LENGTH = 8       # don't cache trivial messages like "yes"
PROMOTE_AFTER_HITS = 3        # mark as "FAQ" once hit count reaches this


class FAQCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._exact = OrderedDict()
        self._embeddings = {}
        self._embed_fn = None
        self._load()

    def set_embed_function(self, embed_fn):
        """Inject embedding function from engine to avoid circular import."""
        self._embed_fn = embed_fn

    def _normalize(self, q):
        q = q.lower().strip()
        q = re.sub(r'[^\w\s]', ' ', q)
        q = re.sub(r'\s+', ' ', q)
        return q

    def _is_cacheable(self, question, intent):
        if intent not in ("troubleshoot", None):
            return False
        if len(question.strip()) < MIN_QUESTION_LENGTH:
            return False
        skip_words = ["yes", "no", "ok", "okay", "thanks", "tried that", "didn't work"]
        q_lower = question.lower().strip()
        if any(q_lower == w or q_lower.startswith(w + " ") for w in skip_words):
            return False
        return True

    def _cosine(self, a, b):
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = sum(x * x for x in a) ** 0.5
        mag_b = sum(y * y for y in b) ** 0.5
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def get(self, question, category=None):
        """
        Try to retrieve a cached response for this question.
        Returns the cached entry dict or None.
        """
        if not question:
            return None

        norm = self._normalize(question)
        with self._lock:
            # Tier 1: exact match
            key = self._make_key(norm, category)
            if key in self._exact:
                entry = self._exact[key]
                if self._is_expired(entry):
                    logger.debug(f"Cache entry expired: {norm[:40]}")
                    del self._exact[key]
                    self._embeddings.pop(key, None)
                else:
                    self._exact.move_to_end(key)
                    entry["hit_count"] += 1
                    entry["last_hit"] = datetime.utcnow().isoformat()
                    logger.info(f"FAQ CACHE HIT (exact) hits={entry['hit_count']} q={norm[:50]}")
                    self._save_async()
                    return {**entry, "cache_type": "exact"}

            # Tier 2: semantic similarity
            if self._embed_fn:
                try:
                    query_emb = self._embed_fn(question)
                    best_key = None
                    best_score = 0.0
                    for k, emb in self._embeddings.items():
                        if k not in self._exact:
                            continue
                        if category:
                            entry_cat = self._exact[k].get("category")
                            if entry_cat and entry_cat != category:
                                continue
                        score = self._cosine(query_emb, emb)
                        if score > best_score:
                            best_score = score
                            best_key = k
                    if best_key and best_score >= SIMILARITY_THRESHOLD:
                        entry = self._exact[best_key]
                        if not self._is_expired(entry):
                            self._exact.move_to_end(best_key)
                            entry["hit_count"] += 1
                            entry["last_hit"] = datetime.utcnow().isoformat()
                            logger.info(f"FAQ CACHE HIT (semantic, score={best_score:.3f}) hits={entry['hit_count']} q={norm[:50]}")
                            self._save_async()
                            return {**entry, "cache_type": "semantic", "similarity": round(best_score, 3)}
                except Exception as e:
                    logger.warning(f"Semantic cache lookup failed: {e}")

        return None

    def put(self, question, response, category=None, kb_sources=None, intent=None):
        """Store a Q/A pair in the cache."""
        if not self._is_cacheable(question, intent):
            return

        norm = self._normalize(question)
        key = self._make_key(norm, category)

        with self._lock:
            entry = {
                "question": question,
                "normalized": norm,
                "response": response,
                "category": category,
                "kb_sources": kb_sources or [],
                "hit_count": 1,
                "created_at": datetime.utcnow().isoformat(),
                "last_hit": datetime.utcnow().isoformat(),
            }
            self._exact[key] = entry
            self._exact.move_to_end(key)

            if self._embed_fn:
                try:
                    self._embeddings[key] = self._embed_fn(question)
                except Exception as e:
                    logger.warning(f"Failed to embed for cache: {e}")

            while len(self._exact) > MAX_CACHE_SIZE:
                evict_key, _ = self._exact.popitem(last=False)
                self._embeddings.pop(evict_key, None)
                logger.debug(f"Cache evicted: {evict_key}")

            logger.info(f"FAQ CACHE STORE q={norm[:50]} category={category}")
            self._save_async()

    def stats(self):
        with self._lock:
            total_entries = len(self._exact)
            total_hits = sum(e["hit_count"] for e in self._exact.values())
            faqs = [
                {
                    "question": e["question"],
                    "category": e["category"],
                    "hit_count": e["hit_count"],
                    "last_hit": e["last_hit"],
                }
                for e in self._exact.values()
                if e["hit_count"] >= PROMOTE_AFTER_HITS
            ]
            faqs.sort(key=lambda f: f["hit_count"], reverse=True)
            return {
                "total_entries": total_entries,
                "total_hits": total_hits,
                "max_size": MAX_CACHE_SIZE,
                "similarity_threshold": SIMILARITY_THRESHOLD,
                "trending_faqs": faqs[:20],
            }

    def clear(self):
        with self._lock:
            self._exact.clear()
            self._embeddings.clear()
            self._save_async()
        logger.info("FAQ cache cleared")

    def _make_key(self, normalized, category):
        return f"{category or 'any'}::{normalized}"

    def _is_expired(self, entry):
        try:
            last = datetime.fromisoformat(entry["last_hit"])
            age_hours = (datetime.utcnow() - last).total_seconds() / 3600
            return age_hours > CACHE_TTL_HOURS
        except Exception:
            return False

    def _save_async(self):
        threading.Thread(target=self._save, daemon=True).start()

    def _save(self):
        try:
            with self._lock:
                data = {
                    "entries": dict(self._exact),
                    "embeddings": {k: v for k, v in self._embeddings.items()},
                    "saved_at": datetime.utcnow().isoformat(),
                }
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save FAQ cache: {e}")

    def _load(self):
        if not CACHE_FILE.exists():
            return
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            entries = data.get("entries", {})
            self._exact = OrderedDict(entries)
            self._embeddings = data.get("embeddings", {})
            logger.info(f"FAQ cache loaded: {len(self._exact)} entries")
        except Exception as e:
            logger.error(f"Failed to load FAQ cache: {e}")


faq_cache = FAQCache()