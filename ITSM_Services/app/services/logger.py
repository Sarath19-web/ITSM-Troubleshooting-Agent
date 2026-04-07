"""
Structured logging service for ITSM Agent.
Logs every operation from application startup to file + console.
JSONL format for easy parsing by log aggregators (Splunk, ELK, Datadog).
"""
import json
import logging
import os
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

APP_LOG = LOG_DIR / "app.log"
PIPELINE_LOG = LOG_DIR / "pipeline.jsonl"
ERROR_LOG = LOG_DIR / "errors.log"
ACCESS_LOG = LOG_DIR / "access.jsonl"


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_obj.update(record.extra_data)
        return json.dumps(log_obj)


class HumanFormatter(logging.Formatter):
    """Human-readable format for console + app.log."""
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"
    RESET = "\033[0m"

    def format(self, record):
        ts = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        color = {
            "DEBUG": self.GRAY,
            "INFO": self.GREEN,
            "WARNING": self.YELLOW,
            "ERROR": self.RED,
            "CRITICAL": self.RED,
        }.get(level, "")
        msg = record.getMessage()
        location = f"{record.module}.{record.funcName}:{record.lineno}"
        return f"{color}[{ts}] {level:8s}{self.RESET} {self.BLUE}{location:40s}{self.RESET} {msg}"


def setup_logging(level=logging.INFO):
    """Initialize all loggers. Call once at app startup."""
    root = logging.getLogger("itsm")
    root.setLevel(level)
    root.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(HumanFormatter())
    root.addHandler(console)

    app_handler = RotatingFileHandler(APP_LOG, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
    app_handler.setLevel(level)
    app_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)-8s %(name)s.%(funcName)s:%(lineno)d - %(message)s"))
    root.addHandler(app_handler)

    error_handler = RotatingFileHandler(ERROR_LOG, maxBytes=5*1024*1024, backupCount=5, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root.addHandler(error_handler)

    return root


def get_logger(name):
    return logging.getLogger(f"itsm.{name}")


def log_pipeline_event(event_type, session_id=None, data=None):
    """Append a structured event to pipeline.jsonl for analytics/replay."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "session_id": session_id,
        "data": data or {},
    }
    try:
        with open(PIPELINE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        get_logger("logger").error(f"Failed to write pipeline log: {e}")


def log_access(method, path, status, duration_ms, session_id=None, extra=None):
    """Log API access entry."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "method": method,
        "path": path,
        "status": status,
        "duration_ms": round(duration_ms, 2),
        "session_id": session_id,
    }
    if extra:
        entry.update(extra)
    try:
        with open(ACCESS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


class Timer:
    """Context manager to time operations."""
    def __init__(self, logger, operation, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start = None

    def __enter__(self):
        self.start = time.time()
        self.logger.debug(f"START {self.operation} {self.context if self.context else ''}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (time.time() - self.start) * 1000
        if exc_type:
            self.logger.error(f"FAIL  {self.operation} after {elapsed:.1f}ms: {exc_val}")
        else:
            self.logger.info(f"DONE  {self.operation} in {elapsed:.1f}ms {self.context if self.context else ''}")
        self.elapsed_ms = elapsed
        return False