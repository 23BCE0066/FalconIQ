"""
app/api/common — Shared API infrastructure.

Every reusable API component lives here so that version folders (v1, v2, ...)
contain only routers and import from this package.

Exports:
    - RequestContext         — Per-request timing + envelope builder
    - SuccessEnvelope        — Standard success response wrapper
    - ErrorEnvelope          — Standard error response wrapper
    - ResponseMapper         — SQLModel → DTO converters
    - PageRequest            — Pagination query params
    - PageResponse           — Paginated response container
    - CustomerFilters        — Customer list filters
    - TransactionFilters     — Transaction list filters
    - AlertFilters           — Alert list filters
    - register_exception_handlers — Registers all HTTP exception handlers
"""
from app.api.common.response_envelope import RequestContext, SuccessEnvelope, ErrorEnvelope
from app.api.common.response_mapper import ResponseMapper
from app.api.common.pagination import PageRequest, PageResponse
from app.api.common.filters import CustomerFilters, TransactionFilters, AlertFilters
from app.api.common.exceptions import register_exception_handlers

__all__ = [
    "RequestContext",
    "SuccessEnvelope",
    "ErrorEnvelope",
    "ResponseMapper",
    "PageRequest",
    "PageResponse",
    "CustomerFilters",
    "TransactionFilters",
    "AlertFilters",
    "register_exception_handlers",
]
