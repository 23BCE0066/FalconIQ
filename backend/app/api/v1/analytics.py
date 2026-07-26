"""
Router: Analytics

GET /api/v1/analytics/risk        — Risk distribution and KYC breakdown
GET /api/v1/analytics/trends      — Transaction and alert trends over time
GET /api/v1/analytics/rules       — AML rule trigger analytics
GET /api/v1/analytics/countries   — Country-level distribution analytics
GET /api/v1/analytics/customers   — Customer segment and risk analytics
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, File, UploadFile
import pandas as pd
import io

from app.api.common.response_envelope import RequestContext, get_request_context
from app.core.dependencies import get_analytics_service
from app.logging.logger import get_logger
from app.services.analytics import AnalyticsService

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/analytics/risk",
    summary="Risk analytics",
    description=(
        "Returns risk distribution analytics including customer count per risk level, "
        "average risk score, high-risk percentage, and KYC status breakdown."
    ),
    response_description="Risk analytics payload.",
    tags=["Analytics"],
    responses={
        200: {"description": "Risk analytics retrieved successfully."},
    },
)
async def get_risk_analytics(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    analytics_svc: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> dict:
    """Risk distribution and classification analytics."""
    data = analytics_svc.get_risk_analytics()
    logger.info("risk_analytics_served", request_id=ctx.request_id)
    return ctx.ok(data.model_dump())


@router.get(
    "/analytics/trends",
    summary="Transaction and alert trends",
    description=(
        "Returns daily transaction counts, alert creation counts, and transaction volumes "
        "for the specified look-back window. Used for trend charts."
    ),
    response_description="Trends analytics payload.",
    tags=["Analytics"],
    responses={
        200: {"description": "Trends analytics retrieved successfully."},
        422: {"description": "Invalid days parameter."},
    },
)
async def get_trends_analytics(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    analytics_svc: Annotated[AnalyticsService, Depends(get_analytics_service)],
    days: int = Query(
        default=30,
        ge=7,
        le=365,
        description="Look-back window in days (7–365)",
    ),
) -> dict:
    """Daily transaction and alert trend data for the specified period."""
    data = analytics_svc.get_trends_analytics(days=days)
    logger.info("trends_analytics_served", request_id=ctx.request_id, days=days)
    return ctx.ok(data.model_dump())


@router.get(
    "/analytics/rules",
    summary="AML rule analytics",
    description=(
        "Returns analytics on triggered AML rules including trigger counts, "
        "percentages, and detection type breakdown."
    ),
    response_description="Rules analytics payload.",
    tags=["Analytics"],
    responses={
        200: {"description": "Rules analytics retrieved successfully."},
    },
)
async def get_rules_analytics(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    analytics_svc: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> dict:
    """AML rule trigger analytics with percentages."""
    data = analytics_svc.get_rules_analytics()
    logger.info("rules_analytics_served", request_id=ctx.request_id)
    return ctx.ok(data.model_dump())


@router.get(
    "/analytics/countries",
    summary="Country distribution analytics",
    description=(
        "Returns per-country transaction and alert analytics including total volume, "
        "transaction counts, and alert counts. Also returns the list of high-risk countries "
        "detected and the cross-border transaction percentage."
    ),
    response_description="Country analytics payload.",
    tags=["Analytics"],
    responses={
        200: {"description": "Country analytics retrieved successfully."},
    },
)
async def get_country_analytics(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    analytics_svc: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> dict:
    """Country-level transaction and alert analytics."""
    data = analytics_svc.get_country_analytics()
    logger.info("country_analytics_served", request_id=ctx.request_id)
    return ctx.ok(data.model_dump())


@router.get(
    "/analytics/customers",
    summary="Customer analytics",
    description=(
        "Returns customer breakdown analytics by segment, KYC verification status, "
        "and risk classification. Also returns the top high-risk customers."
    ),
    response_description="Customer analytics payload.",
    tags=["Analytics"],
    responses={
        200: {"description": "Customer analytics retrieved successfully."},
    },
)
async def get_customer_analytics(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    analytics_svc: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> dict:
    """Customer segment, KYC, and risk level analytics."""
    data = analytics_svc.get_customer_analytics()
    logger.info("customer_analytics_served", request_id=ctx.request_id)
    return ctx.ok(data.model_dump())

@router.get(
    "/analytics/models",
    summary="ML models analytics",
    description="Returns the list of deployed ML models and their performance metrics.",
    response_description="Models analytics payload.",
    tags=["Analytics"],
    responses={
        200: {"description": "Models analytics retrieved successfully."},
    },
)
async def get_models_analytics(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    analytics_svc: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> dict:
    """Registered ML models and performance."""
    data = analytics_svc.get_models_analytics()
    logger.info("models_analytics_served", request_id=ctx.request_id)
    return ctx.ok(data.model_dump())

@router.get(
    "/analytics/datasets",
    summary="Datasets analytics",
    description="Returns the list of datasets and their metadata.",
    response_description="Datasets analytics payload.",
    tags=["Analytics"],
    responses={
        200: {"description": "Datasets analytics retrieved successfully."},
    },
)
async def get_datasets_analytics(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    analytics_svc: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> dict:
    """Registered datasets and metadata."""
    data = analytics_svc.get_datasets_analytics(user_id=ctx.user_id)
    logger.info("datasets_analytics_served", request_id=ctx.request_id)
    return ctx.ok(data.model_dump())


@router.post(
    "/datasets/upload",
    summary="Upload CSV Dataset",
    description="Uploads a user custom CSV dataset into the AML analytics engine.",
    tags=["Analytics"],
)
async def upload_dataset(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    file: UploadFile = File(...),
    analytics_svc: Annotated[AnalyticsService, Depends(get_analytics_service)] = None,
) -> dict:
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
        records = len(df)
    except Exception:
        records = len(content.splitlines()) - 1
        if records < 0:
            records = 0
    size_bytes = len(content)
    dto = analytics_svc.add_uploaded_dataset(file.filename or "custom_dataset.csv", records, size_bytes, ds_type="Uploaded CSV", user_id=ctx.user_id)
    logger.info("dataset_uploaded", filename=file.filename, records=records, size_bytes=size_bytes, user_id=ctx.user_id)
    return ctx.ok(dto.model_dump())


@router.delete(
    "/datasets/{dataset_name}",
    summary="Delete uploaded dataset",
    description="Removes a user-uploaded dataset from the system by name.",
    tags=["Analytics"],
    responses={
        200: {"description": "Dataset deleted successfully."},
        404: {"description": "Dataset not found."},
    },
)
async def delete_dataset(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    dataset_name: str,
    analytics_svc: Annotated[AnalyticsService, Depends(get_analytics_service)] = None,
) -> dict:
    """Deletes an uploaded dataset by name."""
    import urllib.parse
    decoded_name = urllib.parse.unquote(dataset_name)
    success = analytics_svc.delete_uploaded_dataset(decoded_name, user_id=ctx.user_id)
    if success:
        logger.info("dataset_deleted", dataset_name=decoded_name, user_id=ctx.user_id)
        return ctx.ok({"deleted": decoded_name, "status": "removed"})
    return ctx.ok({"deleted": decoded_name, "status": "not_found"})

