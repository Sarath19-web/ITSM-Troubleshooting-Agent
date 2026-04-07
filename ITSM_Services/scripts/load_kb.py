import sys, os, re, time, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from pathlib import Path
from app.config import DB_PATH, KB_PATH, EMBEDDING_MODEL

CATEGORY_MAP = {
    "vpn": "Network & VPN", "network": "Network & VPN", "wifi": "Network & VPN",
    "email": "Email & Calendar", "outlook": "Email & Calendar", "calendar": "Email & Calendar",
    "password": "Account & Access", "account": "Account & Access", "lockout": "Account & Access",
    "printer": "Printer & Peripherals", "print": "Printer & Peripherals",
    "performance": "Performance", "laptop": "Performance", "slow": "Performance",
    "software": "Software & Apps", "install": "Software & Apps", "teams": "Software & Apps",
    "hardware": "Hardware", "security": "Security",
}


def detect_category(filename, content):
    fl = filename.lower()
    for key, cat in CATEGORY_MAP.items():
        if key in fl:
            return cat
    cl = content[:500].lower()
    for key, cat in CATEGORY_MAP.items():
        if key in cl:
            return cat
    return "Other"


def detect_section(text):
    tl = text.lower()
    if any(w in tl for w in ["troubleshooting steps", "step 1", "step 2"]):
        return "troubleshooting"
    if any(w in tl for w in ["when to escalate", "escalat"]):
        return "escalation_criteria"
    if any(w in tl for w in ["common symptoms", "symptom"]):
        return "symptoms"
    if "resolution rate" in tl:
        return "stats"
    return "general"


def load_and_index():
    print("=" * 60)
    print("  ITSM KB Document Loader")
    print("=" * 60)

    if not os.path.exists(KB_PATH):
        print(f"  KB path not found: {KB_PATH}")
        return

    files = list(Path(KB_PATH).glob("*.md"))
    if not files:
        print("  No KB articles found.")
        return

    print(f"\n  Found {len(files)} KB articles:")
    all_docs = []
    for fp in sorted(files):
        try:
            docs = TextLoader(str(fp), encoding="utf-8").load()
            category = detect_category(fp.name, docs[0].page_content)
            kb_id = fp.stem.split("_")[0] if "_" in fp.stem else fp.stem
            for doc in docs:
                doc.metadata["source"] = str(fp)
                doc.metadata["kb_id"] = kb_id
                doc.metadata["category"] = category
                doc.metadata["filename"] = fp.name
            all_docs.extend(docs)
            print(f"    {fp.name} → {category}")
        except Exception as e:
            print(f"    {fp.name} → ERROR: {e}")

    print(f"\n  Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=80,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "]
    )
    chunks = splitter.split_documents(all_docs)

    for i, c in enumerate(chunks):
        c.metadata["chunk_index"] = i
        c.metadata["section_type"] = detect_section(c.page_content)

    print(f"  {len(chunks)} chunks created")

    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)

    print(f"  Embedding with {EMBEDDING_MODEL}...")
    t = time.time()
    emb = OllamaEmbeddings(model=EMBEDDING_MODEL)
    db = Chroma.from_documents(chunks, emb, persist_directory=DB_PATH)
    print(f"  Done in {time.time()-t:.1f}s")
    print(f"  {len(chunks)} vectors stored in {DB_PATH}")
    print(f"\n  Ready. Start the agent: python run_api.py")


if __name__ == "__main__":
    load_and_index()
