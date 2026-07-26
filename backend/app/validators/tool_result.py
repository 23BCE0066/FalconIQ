"""
Validator: ToolResultValidator

Validates ToolResult objects after each tool completes.
Prevents downstream tools from consuming corrupted or incomplete outputs
from a prior step.
"""
from app.core.exceptions import ValidationException
from app.schemas.tool_result import ToolResult


class ToolResultValidator:
    """Validates ToolResult correctness before recording into ExecutionContext."""

    def validate(self, result: ToolResult) -> None:
        """
        Validates a ToolResult object.

        Checks:
        1. tool_name is not empty.
        2. confidence is within [0.0, 1.0].
        3. execution_time_ms is non-negative.
        4. Failed results must have at least one error message.
        """
        if not result.tool_name:
            raise ValidationException("ToolResult is missing a tool_name.")

        if not (0.0 <= result.confidence <= 1.0):
            raise ValidationException(
                f"ToolResult confidence '{result.confidence}' from '{result.tool_name}' "
                f"is outside valid range [0.0, 1.0]."
            )

        if result.execution_time_ms < 0:
            raise ValidationException(
                f"ToolResult execution_time_ms '{result.execution_time_ms}' "
                f"from '{result.tool_name}' cannot be negative."
            )

        if not result.success and not result.errors:
            raise ValidationException(
                f"ToolResult from '{result.tool_name}' reports failure but provides no error messages."
            )


class DatasetValidator:
    """
    Validates that a loaded DataFrame meets minimum requirements
    before feature engineering or rule checks proceed.
    """

    REQUIRED_COLUMNS = {
        "transaction_id",
        "sender_id",
        "receiver_id",
        "amount",
        "timestamp",
        "type",
        "country",
    }

    def validate_transaction_df(self, df: object) -> None:
        """
        Validates that a DataFrame has required columns and is not empty.
        Raises ValidationException on failure.

        Args:
            df: A pandas DataFrame instance.
        """
        try:
            import pandas as pd
            if not isinstance(df, pd.DataFrame):
                raise ValidationException("Dataset is not a valid pandas DataFrame.")

            if df.empty:
                raise ValidationException("Dataset is empty — no transactions to analyse.")

            missing = self.REQUIRED_COLUMNS - set(df.columns)
            if missing:
                raise ValidationException(
                    f"Transaction DataFrame is missing required columns: {sorted(missing)}"
                )
        except ImportError as exc:
            raise ValidationException(f"pandas is not available: {exc}") from exc
