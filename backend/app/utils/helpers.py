"""General-purpose utility functions."""
from datetime import datetime, timezone
from typing import Any, Optional
import re
import hashlib


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def paginate(query, page: int = 1, per_page: int = 20) -> tuple[Any, dict]:
    """Apply pagination to a SQLAlchemy query. Returns (items, meta)."""
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
    }


def sanitize_regex(pattern: str) -> Optional[str]:
    """Return pattern if valid regex, else None."""
    try:
        re.compile(pattern)
        return pattern
    except re.error:
        return None


def mask_secret(value: str, visible: int = 4) -> str:
    """Mask a secret value: 'mypassword' → 'mypa****'."""
    if len(value) <= visible:
        return "*" * len(value)
    return value[:visible] + "*" * (len(value) - visible)


def fingerprint(value: str) -> str:
    """Return a short SHA-256 fingerprint of a string."""
    return hashlib.sha256(value.encode()).hexdigest()[:12]
