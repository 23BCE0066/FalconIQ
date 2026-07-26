"""
Tool: NetworkAnalyzerTool (Production Implementation)

Performs graph analysis on the transaction dataset to detect complex typologies
like circular movement, layering chains, and suspicious hubs.
"""
from typing import Any, Dict

import pandas as pd

from app.constants import ToolName
from app.interfaces.tools import BaseTool
from app.schemas.execution_context import ExecutionContext
from app.schemas.tool_result import ToolResult
from app.services.dataset import DatasetService
from app.services.graph import GraphService


class NetworkAnalyzerTool(BaseTool):
    """Detects multi-hop AML typologies using graph analytics."""

    def __init__(self, graph_service: GraphService) -> None:
        self._service = graph_service

    @property
    def name(self) -> str:
        return ToolName.NETWORK_ANALYZER

    @property
    def description(self) -> str:
        return (
            "Analyzes the transaction graph to detect multi-hop typologies like "
            "circular transactions, layering chains, and suspicious hubs. "
            "Requires dataset tool output."
        )

    async def _run(self, context: ExecutionContext) -> ToolResult:
        df: pd.DataFrame | None = context.get_df(DatasetService.DF_TRANSACTIONS)
        
        if df is None or df.empty:
            return ToolResult.failure(self.name, "Dataset is empty. Cannot build graph.")
            
        metrics = self._service.analyze_network(df)
        
        context.set_var("network_metrics", metrics)
        
        # Summarize for explanation
        cycles = metrics.get("circular_patterns_count", 0)
        chains = metrics.get("layering_chains_count", 0)
        hubs = len(metrics.get("hubs", []))
        
        findings = []
        if cycles > 0:
            findings.append(f"{cycles} circular transaction patterns")
        if chains > 0:
            findings.append(f"{chains} potential layering chains")
        if hubs > 0:
            findings.append(f"{hubs} highly connected hubs")
            
        if findings:
            explanation = "Graph analysis detected: " + ", ".join(findings) + "."
        else:
            explanation = "Graph analysis found no complex structural typologies."
            
        return ToolResult(
            success=True,
            status="completed",
            tool_name=self.name,
            execution_time_ms=0.0,
            confidence=0.85,
            data=metrics,
            explanation=explanation,
            metadata={"nodes": metrics.get("nodes"), "edges": metrics.get("edges")},
        )
