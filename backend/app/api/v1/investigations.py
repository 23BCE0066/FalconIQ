"""
Router: Investigations (Chat Sessions)
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func, and_

from app.api.common.pagination import PageRequest
from app.api.common.response_envelope import RequestContext, get_request_context
from app.api.common.response_mapper import ResponseMapper, InvestigationSummaryDTO
from app.database.engine import get_session
from app.database.models.session import AgentSession
from app.logging.logger import get_logger
from pydantic import BaseModel

router = APIRouter()
logger = get_logger(__name__)


class InvestigationStatsDTO(BaseModel):
    total: int
    completed: int
    failed: int
    running: int
    avg_time_ms: int


@router.get(
    "/investigations/stats",
    summary="Get investigation statistics",
    tags=["Investigations"],
)
async def get_investigation_stats(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    db: Annotated[Session, Depends(get_session)],
) -> dict:
    stmt = select(AgentSession.status, func.count(), func.avg(AgentSession.total_execution_time_ms)).group_by(AgentSession.status)
    rows = db.exec(stmt).all()
    
    total = sum(row[1] for row in rows)
    completed = sum(row[1] for row in rows if row[0] == "COMPLETED")
    failed = sum(row[1] for row in rows if row[0] == "FAILED")
    running = sum(row[1] for row in rows if row[0] == "RUNNING")
    
    # Calculate average time from completed sessions
    time_stmt = select(func.avg(AgentSession.total_execution_time_ms)).where(AgentSession.total_execution_time_ms.isnot(None)) # type: ignore
    avg_time = db.exec(time_stmt).one() or 0
    
    stats = InvestigationStatsDTO(
        total=total,
        completed=completed,
        failed=failed,
        running=running,
        avg_time_ms=int(avg_time),
    )
    return ctx.ok(stats.model_dump())


@router.get(
    "/investigations",
    summary="List investigations",
    tags=["Investigations"],
)
async def list_investigations(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    pagination: Annotated[PageRequest, Depends()],
    db: Annotated[Session, Depends(get_session)],
    status: str = None,
    q: str = None,
) -> dict:
    conditions = []
    if status:
        conditions.append(AgentSession.status == status)
    if q:
        # Simple substring search in query
        conditions.append(AgentSession.query.ilike(f"%{q}%")) # type: ignore
        
    count_stmt = select(func.count()).select_from(AgentSession)
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total = db.exec(count_stmt).one() or 0
    
    stmt = select(AgentSession).order_by(AgentSession.created_at.desc()) # type: ignore
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.offset(pagination.skip).limit(pagination.limit)
    
    sessions = list(db.exec(stmt).all())
    dtos = [ResponseMapper.investigation_summary(s) for s in sessions]
    
    return ctx.ok(pagination.wrap(dtos, total).model_dump())
