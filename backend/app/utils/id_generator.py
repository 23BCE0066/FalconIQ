"""
Utils: ID generation utilities.

Produces consistently formatted, collision-resistant identifiers for all
domain entities. Uses UUID4 with typed prefixes for human-readable tracing.
"""
import uuid


def generate_id(prefix: str = "") -> str:
    """
    Generates a prefixed UUID4 string identifier.

    Args:
        prefix: Short domain prefix (e.g. 'sess', 'cust', 'txn', 'alert').

    Returns:
        Formatted string: '<prefix>_<uuid4_hex_short>' or raw uuid4 hex.

    Example:
        generate_id("sess")  → "sess_3f2a1b9c"
    """
    uid = uuid.uuid4().hex[:12]
    return f"{prefix}_{uid}" if prefix else uid


def generate_session_id() -> str:
    return generate_id("sess")


def generate_customer_id() -> str:
    return generate_id("cust")


def generate_transaction_id() -> str:
    return generate_id("txn")


def generate_alert_id() -> str:
    return generate_id("alert")


def generate_report_id() -> str:
    return generate_id("rep")


def generate_log_id() -> str:
    return generate_id("log")
