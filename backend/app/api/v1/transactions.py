"""
Router: Transactions

GET /api/v1/transactions          — paginated + filtered list
GET /api/v1/transactions/search   — text + filter search
GET /api/v1/transactions/{id}     — single transaction detail

NOTE: /search must be declared BEFORE /{transaction_id} to avoid
FastAPI treating "search" as a path parameter value.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query

from app.api.common.filters import TransactionFilters
from app.api.common.pagination import PageRequest
from app.api.common.response_envelope import RequestContext, get_request_context
from app.api.common.response_mapper import ResponseMapper
from app.core.dependencies import get_transaction_service
from app.logging.logger import get_logger
from app.services.transaction import TransactionService

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/transactions",
    summary="List transactions",
    description=(
        "Returns a paginated list of financial transactions. Supports filtering by "
        "customer, country, transaction type, amount range, date range, "
        "cross-border flag, and weekend flag."
    ),
    response_description="Paginated transaction list.",
    tags=["Transactions"],
    responses={
        200: {"description": "Transaction list retrieved successfully."},
        422: {"description": "Invalid filter or pagination parameter."},
    },
)
async def list_transactions(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    pagination: Annotated[PageRequest, Depends()],
    filters: Annotated[TransactionFilters, Depends()],
    tx_svc: Annotated[TransactionService, Depends(get_transaction_service)],
) -> dict:
    """
    Paginated transaction list with comprehensive filter support.

    **Filters:**
    - `customer_id` — Filter by sender
    - `country` — ISO 3166-1 alpha-3
    - `tx_type` — TRANSFER | CASH_IN | CASH_OUT | PAYMENT | DEBIT | CREDIT
    - `min_amount` / `max_amount` — Amount range
    - `date_from` / `date_to` — Date range (YYYY-MM-DD)
    - `is_cross_border` — Boolean
    - `is_weekend` — Boolean
    """
    items, total = tx_svc.list_transactions(
        filters=filters,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    dtos = ResponseMapper.transactions(items)

    logger.info(
        "transactions_listed",
        request_id=ctx.request_id,
        total=total,
        page=pagination.page,
    )
    return ctx.ok(pagination.wrap(dtos, total).model_dump())


@router.get(
    "/transactions/search",
    summary="Search transactions",
    description=(
        "Searches transactions by transaction ID, sender ID, or receiver ID prefix. "
        "Optionally combine with any TransactionFilter for precise results."
    ),
    response_description="Paginated search results.",
    tags=["Transactions"],
    responses={
        200: {"description": "Search results retrieved successfully."},
        422: {"description": "Invalid search query or filter parameter."},
    },
)
async def search_transactions(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    pagination: Annotated[PageRequest, Depends()],
    filters: Annotated[TransactionFilters, Depends()],
    tx_svc: Annotated[TransactionService, Depends(get_transaction_service)],
    q: str = Query(
        ...,
        min_length=2,
        max_length=100,
        description="Search term: transaction ID, sender ID, or receiver ID prefix",
    ),
) -> dict:
    """
    Full-text prefix search across transaction identifiers.
    Combine with filters for targeted AML queries.
    """
    items, total = tx_svc.search_transactions(
        query=q,
        filters=filters,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    dtos = ResponseMapper.transactions(items)

    logger.info(
        "transactions_searched",
        request_id=ctx.request_id,
        query=q,
        total=total,
    )
    return ctx.ok(pagination.wrap(dtos, total).model_dump())


@router.get(
    "/transactions/{transaction_id}",
    summary="Get transaction detail",
    description=(
        "Returns the complete details of a single financial transaction by its ID."
    ),
    response_description="Transaction detail.",
    tags=["Transactions"],
    responses={
        200: {"description": "Transaction retrieved successfully."},
        404: {"description": "Transaction not found."},
    },
)
async def get_transaction(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    transaction_id: str = Path(
        ..., description="Transaction ID (e.g. txn_abc123)"
    ),
    tx_svc: Annotated[TransactionService, Depends(get_transaction_service)] = None,
) -> dict:
    """Returns a single transaction by ID."""
    tx = tx_svc.get_transaction(transaction_id)
    dto = ResponseMapper.transaction(tx)

    logger.info(
        "transaction_retrieved",
        request_id=ctx.request_id,
        transaction_id=transaction_id,
    )
    return ctx.ok(dto.model_dump())
