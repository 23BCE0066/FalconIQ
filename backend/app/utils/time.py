"""
Utils: Time and datetime helpers.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Returns the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def format_iso(dt: datetime) -> str:
    """Formats a datetime as ISO 8601 string."""
    return dt.isoformat()


def elapsed_ms(start: float, end: float) -> float:
    """Computes elapsed time in milliseconds between two perf_counter values."""
    return round((end - start) * 1000, 3)
