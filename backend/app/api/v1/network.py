"""
Router: Network

GET /api/v1/network/customer/{customer_id} — Customer-scoped transaction graph
GET /api/v1/network/suspicious             — Global suspicious network detection

Both endpoints return graph-ready JSON (nodes + edges) for D3.js / Cytoscape.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlmodel import Session, or_, select

from app.api.common.response_envelope import RequestContext, get_request_context
from app.api.common.response_mapper import (
    NetworkEdgeDTO,
    NetworkGraphDTO,
    NetworkNodeDTO,
    ResponseMapper,
    SuspiciousNetworkDTO,
)
from app.core.dependencies import (
    get_customer_service,
    get_dataset_service,
    get_graph_service,
)
from app.database.engine import get_session
from app.database.models.customer import Customer
from app.database.models.transaction import Transaction
from app.logging.logger import get_logger
from app.services.customer import CustomerService
from app.services.dataset import DatasetService
from app.services.graph import GraphService

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/network/customer/{customer_id}",
    summary="Customer transaction network",
    description=(
        "Builds and analyses the transaction network for a specific customer. "
        "Returns graph-ready nodes and edges (for D3.js / Cytoscape), plus "
        "detected circular patterns, layering chains, and network hubs."
    ),
    response_description="Customer network graph payload.",
    tags=["Network"],
    responses={
        200: {"description": "Network graph retrieved successfully."},
        404: {"description": "Customer not found."},
    },
)
async def get_customer_network(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    customer_id: str = Path(..., description="Customer ID to analyse"),
    days: int = Query(
        default=90,
        ge=7,
        le=365,
        description="Look-back window in days for network analysis",
    ),
    db: Annotated[Session, Depends(get_session)] = None,
    customer_svc: Annotated[CustomerService, Depends(get_customer_service)] = None,
    dataset_svc: Annotated[DatasetService, Depends(get_dataset_service)] = None,
    graph_svc: Annotated[GraphService, Depends(get_graph_service)] = None,
) -> dict:
    """Customer-scoped transaction network analysis with graph-ready output."""
    # Validate customer exists
    customer_svc.get_customer(customer_id)

    # Load transaction data
    df = dataset_svc.load_transactions(customer_id=customer_id, days=days)

    # Analyse network
    analysis = graph_svc.analyze_network(df)

    # Build graph-ready nodes and edges from the DataFrame
    nodes, edges = _build_graph_payload(df, db, focal_customer_id=customer_id)

    graph = NetworkGraphDTO(
        nodes=nodes,
        edges=edges,
        circular_patterns=analysis.get("circular_patterns", []),
        layering_chains=analysis.get("layering_chains", []),
        hubs=analysis.get("hubs", []),
        total_nodes=len(nodes),
        total_edges=len(edges),
        suspicious_patterns_count=(
            analysis.get("circular_patterns_count", 0)
            + analysis.get("layering_chains_count", 0)
        ),
    )

    logger.info(
        "customer_network_analysed",
        request_id=ctx.request_id,
        customer_id=customer_id,
        nodes=len(nodes),
        edges=len(edges),
    )
    return ctx.ok(graph.model_dump())


@router.get(
    "/network/suspicious",
    summary="Suspicious network detection",
    description=(
        "Performs a global network analysis across all recent transactions to detect "
        "suspicious patterns such as circular fund flows, layering chains, and hub entities. "
        "Returns a graph-ready payload with flagged clusters."
    ),
    response_description="Suspicious network detection payload.",
    tags=["Network"],
    responses={
        200: {"description": "Suspicious network analysis retrieved successfully."},
    },
)
async def get_suspicious_network(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    days: int = Query(
        default=30,
        ge=7,
        le=180,
        description="Look-back window in days",
    ),
    db: Annotated[Session, Depends(get_session)] = None,
    dataset_svc: Annotated[DatasetService, Depends(get_dataset_service)] = None,
    graph_svc: Annotated[GraphService, Depends(get_graph_service)] = None,
) -> dict:
    """Global suspicious network analysis."""
    df = dataset_svc.load_transactions(days=days, limit=5000)
    analysis = graph_svc.analyze_network(df)

    nodes, edges = _build_graph_payload(df, db)

    graph = NetworkGraphDTO(
        nodes=nodes,
        edges=edges,
        circular_patterns=analysis.get("circular_patterns", []),
        layering_chains=analysis.get("layering_chains", []),
        hubs=analysis.get("hubs", []),
        total_nodes=len(nodes),
        total_edges=len(edges),
        suspicious_patterns_count=(
            analysis.get("circular_patterns_count", 0)
            + analysis.get("layering_chains_count", 0)
        ),
    )

    # Most connected entities (top hubs as NetworkNodeDTOs)
    hub_nodes = sorted(nodes, key=lambda n: n.transaction_count, reverse=True)[:5]

    result = SuspiciousNetworkDTO(
        graph=graph,
        risk_clusters=analysis.get("circular_patterns", []),
        most_connected_entities=hub_nodes,
    )

    logger.info(
        "suspicious_network_analysed",
        request_id=ctx.request_id,
        days=days,
        nodes=len(nodes),
        suspicious_patterns=graph.suspicious_patterns_count,
    )
    return ctx.ok(result.model_dump())


# ── Helper ─────────────────────────────────────────────────────────────────────

def _build_graph_payload(df, db: Session, focal_customer_id: str = None):
    """Builds NetworkNodeDTO and NetworkEdgeDTO lists from a transaction DataFrame."""
    if df.empty:
        return [], []

    # Aggregate edges
    edge_map: dict = {}
    node_volume: dict = {}
    node_count: dict = {}

    for _, row in df.iterrows():
        sender = str(row.get("sender_id", ""))
        receiver = str(row.get("receiver_id", ""))
        amount = float(row.get("amount", 0))

        if not sender or not receiver:
            continue

        edge_key = (sender, receiver)
        if edge_key in edge_map:
            edge_map[edge_key]["weight"] += amount
            edge_map[edge_key]["count"] += 1
        else:
            edge_map[edge_key] = {"weight": amount, "count": 1}

        for node_id in (sender, receiver):
            node_volume[node_id] = node_volume.get(node_id, 0) + amount
            node_count[node_id] = node_count.get(node_id, 0) + 1

    # Look up risk levels for known customers
    node_ids = list(node_volume.keys())
    customer_risk_map: dict = {}
    if db and node_ids:
        stmt = select(Customer.customer_id, Customer.risk_category).where(
            Customer.customer_id.in_(node_ids)  # type: ignore[attr-defined]
        )
        for cid, risk in db.exec(stmt).all():
            customer_risk_map[cid] = str(risk.value if hasattr(risk, "value") else risk)

    nodes = [
        NetworkNodeDTO(
            id=node_id,
            label=node_id,
            type="customer" if node_id in customer_risk_map else "external",
            risk_level=customer_risk_map.get(node_id),
            transaction_count=node_count.get(node_id, 0),
            total_volume=round(node_volume.get(node_id, 0), 2),
        )
        for node_id in node_ids
    ]

    edges = [
        NetworkEdgeDTO(
            source=src,
            target=dst,
            weight=round(data["weight"], 2),
            count=data["count"],
        )
        for (src, dst), data in edge_map.items()
    ]

    return nodes, edges
