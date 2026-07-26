"""
Utils: JSON serialization helpers.

Handles non-standard types (datetime, Decimal, Enum) that Python's default
json.dumps rejects, enabling clean structured logging and API serialization.
"""
import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class FalconIQJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for FalconIQ domain objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


def safe_dumps(obj: Any, **kwargs: Any) -> str:
    """Serializes an object to a JSON string using the FalconIQ encoder."""
    return json.dumps(obj, cls=FalconIQJSONEncoder, **kwargs)


def safe_loads(raw: str) -> Any:
    """Deserializes a JSON string, returning None on failure."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
