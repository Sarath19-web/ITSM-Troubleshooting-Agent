import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = str(BASE_DIR / "data" / "db")
KB_PATH = str(BASE_DIR / "data" / "kb_articles")
TICKETS_FILE = str(BASE_DIR / "data" / "tickets.json")
PIPELINE_LOG = str(BASE_DIR / "logs" / "pipeline.jsonl")
LOG_DIR = str(BASE_DIR / "logs")

EMBEDDING_MODEL = "nomic-embed-text"
# LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:1b")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

RETRIEVAL_K = 6
RERANK_TOP_N = 3
MAX_CONTEXT_CHARS = 2000
LLM_NUM_PREDICT = 768
LLM_TEMPERATURE = 0.15
LLM_NUM_CTX = 4096

MAX_TROUBLESHOOT_TURNS = 5

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

TICKET_PRIORITIES = {"P1": "Critical", "P2": "High", "P3": "Medium", "P4": "Low"}
TICKET_CATEGORIES = [
    "Network & VPN", "Email & Calendar", "Hardware", "Software & Apps",
    "Account & Access", "Printer & Peripherals", "Performance", "Security", "Other"
]
