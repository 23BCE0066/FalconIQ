"""
Router: Reports

POST /api/v1/reports/generate          — Generate a new report
GET  /api/v1/reports/{report_id}       — Retrieve a generated report
GET  /api/v1/reports/download/{report_id} — Download report (JSON/Markdown/PDF-stub)

NOTE: /download/{report_id} must be declared BEFORE /{report_id} to prevent
FastAPI treating "download" as a report_id value.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path
from fastapi.responses import PlainTextResponse, Response

from app.api.common.response_envelope import RequestContext, get_request_context
from app.core.dependencies import get_report_service
from app.core.exceptions import ValidationException
from app.logging.logger import get_logger
from app.services.report import ReportRequest, ReportService

router = APIRouter()
logger = get_logger(__name__)

_VALID_REPORT_TYPES = {"risk_summary", "transaction_analysis", "alert_report", "compliance"}
_VALID_FORMATS = {"json", "markdown", "pdf", "doc", "docx"}


@router.post(
    "/reports/generate",
    summary="Generate a report",
    description=(
        "Generates a compliance report of the specified type and format. "
        "Supported types: `risk_summary`, `transaction_analysis`, `alert_report`, `compliance`. "
        "Supported formats: `json`, `markdown`, `pdf` (PDF is a Markdown stub). "
        "Returns the report metadata and content. Use the report_id to download later."
    ),
    response_description="Generated report metadata and content.",
    tags=["Reports"],
    responses={
        200: {"description": "Report generated successfully."},
        400: {"description": "Invalid report type or format."},
    },
)
async def generate_report(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    body: ReportRequest,
    report_svc: Annotated[ReportService, Depends(get_report_service)],
) -> dict:
    """
    Generates a compliance report.

    **Report Types:**
    - `risk_summary` — Customer risk distribution + top rules
    - `transaction_analysis` — Transaction trends + country breakdown
    - `alert_report` — Alert statistics + recent alerts
    - `compliance` — Executive compliance overview

    **Formats:**
    - `json` — Structured JSON data
    - `markdown` — Formatted Markdown document
    - `pdf` — Markdown stub (full PDF rendering in future phase)
    """
    # Validate
    if body.report_type not in _VALID_REPORT_TYPES:
        raise ValidationException(
            f"Invalid report_type '{body.report_type}'. "
            f"Must be one of: {', '.join(sorted(_VALID_REPORT_TYPES))}."
        )
    if body.format.lower() not in _VALID_FORMATS:
        raise ValidationException(
            f"Invalid format '{body.format}'. Must be one of: {', '.join(sorted(_VALID_FORMATS))}."
        )

    report = report_svc.generate_report(body, user_id=ctx.user_id)

    logger.info(
        "report_generated",
        request_id=ctx.request_id,
        report_id=report.report_id,
        report_type=body.report_type,
        format=body.format,
        user_id=ctx.user_id,
    )
    return ctx.ok(report.model_dump())


@router.get(
    "/reports/download/{report_id}",
    summary="Download report",
    description=(
        "Downloads a previously generated report. Returns JSON data, Markdown text, "
        "or a PDF-stub Markdown document depending on the report format."
    ),
    tags=["Reports"],
    responses={
        200: {"description": "Report downloaded successfully."},
        404: {"description": "Report not found."},
    },
)
async def download_report(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    report_id: str = Path(..., description="Report ID (e.g. rpt_abc123)"),
    report_svc: Annotated[ReportService, Depends(get_report_service)] = None,
) -> Response:
    """
    Downloads a generated report.

    Content-Type varies by format:
    - `json` → application/json
    - `markdown` → text/markdown
    - `pdf` → text/plain (stub)
    """
    report = report_svc.download_report(report_id)
    if not report:
        raise ValidationException(f"Report '{report_id}' not found.")

    import json

    if report.format == "json":
        content = json.dumps(report.content, indent=2, default=str)
        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{report_id}.json"'
            },
        )
    elif report.format == "pdf":
        from app.utils.pdf_generator import make_simple_pdf
        pdf_bytes = make_simple_pdf(report.markdown or "")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{report_id}.pdf"'
            },
        )
    elif report.format in ("doc", "docx"):
        html_doc = f"<html><head><meta charset='utf-8'><title>{report_id}</title><style>body {{ font-family: Calibri, sans-serif; line-height: 1.5; padding: 20px; }} h1, h2, h3 {{ color: #1e3a8a; }} pre {{ background: #f1f5f9; padding: 10px; border-radius: 5px; }}</style></head><body><h1>AML Compliance Report</h1><pre style='white-space: pre-wrap; font-family: Calibri, sans-serif;'>{report.markdown or ''}</pre></body></html>"
        return Response(
            content=html_doc.encode("utf-8"),
            media_type="application/msword",
            headers={
                "Content-Disposition": f'attachment; filename="{report_id}.doc"'
            },
        )
    elif report.format == "markdown":
        return PlainTextResponse(
            content=report.markdown or "",
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{report_id}.md"'
            },
        )
    else:
        content = json.dumps(report.content, indent=2, default=str)
        return Response(content=content, media_type="application/json")


@router.get(
    "/reports/{report_id}",
    summary="Get report metadata",
    description="Returns metadata and content of a previously generated report.",
    response_description="Report metadata and content.",
    tags=["Reports"],
    responses={
        200: {"description": "Report retrieved successfully."},
        404: {"description": "Report not found."},
    },
)
async def get_report(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    report_id: str = Path(..., description="Report ID (e.g. rpt_abc123)"),
    report_svc: Annotated[ReportService, Depends(get_report_service)] = None,
) -> dict:
    """Retrieves a generated report by ID."""
    report = report_svc.get_report(report_id)
    if not report:
        raise ValidationException(f"Report '{report_id}' not found.")

    logger.info(
        "report_retrieved",
        request_id=ctx.request_id,
        report_id=report_id,
    )
    return ctx.ok(report.model_dump())

from app.api.common.pagination import PageRequest

@router.get(
    "/reports",
    summary="List generated reports",
    description="Returns a paginated list of previously generated reports.",
    response_description="Paginated reports list.",
    tags=["Reports"],
    responses={
        200: {"description": "Reports list retrieved successfully."},
    },
)
async def list_reports(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    pagination: Annotated[PageRequest, Depends()],
    report_svc: Annotated[ReportService, Depends(get_report_service)],
) -> dict:
    """List all reports."""
    reports = report_svc.list_reports(user_id=ctx.user_id)
    total = len(reports)
    
    # In-memory pagination
    start = pagination.skip
    end = start + pagination.limit
    paginated_reports = reports[start:end]
    
    # We can omit the content field to save bandwidth, but ReportDTO is small enough if content is none
    dtos = [r for r in paginated_reports]
    
    logger.info("reports_listed", request_id=ctx.request_id, total=total)
    return ctx.ok(pagination.wrap(dtos, total).model_dump())
