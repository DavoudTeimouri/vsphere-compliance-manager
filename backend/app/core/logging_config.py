"""
Structured logging configuration for VCM.
Produces JSON logs in production, human-readable in development.
"""
import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any
import os


class JSONFormatter(logging.Formatter):
    """Outputs each log record as a single JSON line."""

    LEVEL_MAP = {
        logging.DEBUG:    "DEBUG",
        logging.INFO:     "INFO",
        logging.WARNING:  "WARNING",
        logging.ERROR:    "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        log: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level":     self.LEVEL_MAP.get(record.levelno, "UNKNOWN"),
            "logger":    record.name,
            "message":   record.getMessage(),
            "module":    record.module,
            "function":  record.funcName,
            "line":      record.lineno,
        }
        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            log.update(record.extra)
        return json.dumps(log, default=str)


class HumanFormatter(logging.Formatter):
    """Colored, readable output for development."""

    COLORS = {
        "DEBUG":    "\033[36m",   # cyan
        "INFO":     "\033[32m",   # green
        "WARNING":  "\033[33m",   # yellow
        "ERROR":    "\033[31m",   # red
        "CRITICAL": "\033[35m",   # magenta
        "RESET":    "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        level = record.levelname
        color = self.COLORS.get(level, "")
        reset = self.COLORS["RESET"]
        ts = datetime.now().strftime("%H:%M:%S")
        return (
            f"{color}{ts} [{level:8s}] {record.name}: "
            f"{record.getMessage()}{reset}"
        )


def setup_logging() -> None:
    """
    Configure root logger based on APP_ENV and LOG_LEVEL.

    In production  (APP_ENV=production):  JSON formatter → stdout
    In development (APP_ENV=development): Human formatter → stdout

    Usage:
        from app.core.logging_config import setup_logging
        setup_logging()
    """
    env       = os.getenv("APP_ENV", "production")
    level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    level     = getattr(logging, level_str, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if env == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(HumanFormatter())

    # Root logger
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.getLogger("vcm").info(
        "Logging initialised",
        extra={"env": env, "level": level_str}
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named child of the vcm root logger."""
    return logging.getLogger(f"vcm.{name}")
