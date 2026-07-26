"""
Tool: DatasetTool (Production Implementation)

Replaces the Phase 3 stub. Delegates all data loading to DatasetService,
caches results in ExecutionContext, and validates the loaded DataFrame.
"""
import time
from typing import Optional

from app.constants import ToolName
from app.interfaces.tools import BaseTool
from app.schemas.execution_context import ExecutionContext
from app.schemas.tool_result import ToolResult
from app.services.dataset import DatasetService
from app.validators.tool_result import DatasetValidator


class DatasetTool(BaseTool):
    """
    Loads and filters financial transaction data.

    Caches the result DataFrame in ExecutionContext so downstream tools
    (Feature, Rule Engine, ML) never reload the same data.
    """

    def __init__(self, dataset_service: DatasetService) -> None:
        self._service = dataset_service
        self._validator = DatasetValidator()

    @property
    def name(self) -> str:
        return ToolName.DATASET

    @property
    def description(self) -> str:
        return (
            "Loads and filters transaction and customer records from the database. "
            "Applies date, customer, country, amount and type filters. "
            "Caches results in context for reuse. Always the first tool."
        )

    async def _run(self, context: ExecutionContext) -> ToolResult:
        # Return cached result if already loaded (same context = same query)
        if context.has_df(DatasetService.DF_TRANSACTIONS):
            cached = context.get_df(DatasetService.DF_TRANSACTIONS)
            return ToolResult(
                success=True,
                status="completed",
                tool_name=self.name,
                execution_time_ms=0.0,
                confidence=1.0,
                data={"record_count": len(cached), "source": "cache"},
                explanation=f"Returned {len(cached)} cached transaction records.",
                metadata={"cached": True},
            )

        # Extract filters from the execution plan
        filters = (
            context.execution_plan.filters
            if context.execution_plan and context.execution_plan.filters
            else None
        )
        days = filters.days if filters else None
        customer_id = filters.customer_id if filters else None
        country = filters.country if filters else None
        min_amount = filters.min_amount if filters else None
        max_amount = filters.max_amount if filters else None

        import time
        t_db_start = time.perf_counter()
        df = self._service.load_transactions(
            days=days,
            customer_id=customer_id,
            country=country,
            min_amount=min_amount,
            max_amount=max_amount,
        )
        context.add_metric("database_time_ms", (time.perf_counter() - t_db_start) * 1000)

        # Validate schema before caching
        self._validator.validate_transaction_df(df)

        # Cache in context
        context.set_df(DatasetService.DF_TRANSACTIONS, df)
        context.set_var("dataset_loaded", True)
        context.set_var("record_count", len(df))
        context.set_var("filter_days", days)
        context.set_var("filter_customer_id", customer_id)

        filter_desc = ", ".join(
            f"{k}={v}"
            for k, v in [("days", days), ("customer_id", customer_id),
                          ("country", country), ("min_amount", min_amount)]
            if v is not None
        ) or "none"

        return ToolResult(
            success=True,
            status="completed",
            tool_name=self.name,
            execution_time_ms=0.0,
            confidence=1.0,
            data={
                "record_count": len(df),
                "filters_applied": filter_desc,
                "columns": list(df.columns),
                "date_range": {
                    "min": str(df["timestamp"].min()) if not df.empty else None,
                    "max": str(df["timestamp"].max()) if not df.empty else None,
                },
            },
            explanation=(
                f"Loaded {len(df):,} transactions with filters: {filter_desc}."
            ),
            metadata={"cached": False, "limit": 10_000},
        )
