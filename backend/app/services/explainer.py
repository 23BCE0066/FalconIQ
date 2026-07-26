"""
Service: ExplainerService

Delegates the generation of human-readable AML explanations to Gemini.
Consumes structured JSON context (never raw DataFrames) and produces a
structured ExplanationResponse.
"""
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.core.exceptions import LLMException
from app.interfaces.services import BaseService
from app.logging.logger import get_logger
from app.services.gemini import GeminiService
from app.utils.json import safe_dumps

logger = get_logger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "explainer.md"


class ExplanationResponse(BaseModel):
    """Structured output expected from Gemini for explanations."""
    executive_summary: str = Field(..., description="High-level 2-3 sentence summary.")
    detailed_explanation: str = Field(..., description="Thorough explanation of findings.")
    compliance_recommendation: str = Field(..., description="Specific recommended action (e.g. APPROVE, ESCALATE).")
    next_steps: List[str] = Field(..., description="List of actionable next steps.")


class ExplainerService(BaseService):
    """
    Generates compliance narratives using Gemini.
    """

    def __init__(self, gemini_service: GeminiService) -> None:
        self._gemini = gemini_service
        self._system_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        if not _PROMPT_PATH.exists():
            logger.error("explainer_prompt_missing", path=str(_PROMPT_PATH))
            return "You are an AML explainability engine. Explain the provided JSON data clearly."
        return _PROMPT_PATH.read_text(encoding="utf-8").strip()

    def generate_explanation(self, context_payload: Dict[str, Any]) -> ExplanationResponse:
        """
        Sends the structured context payload to Gemini and returns a typed explanation.
        """
        user_prompt = f"Please explain the following AML investigation findings:\n\n{safe_dumps(context_payload, indent=2)}"
        
        try:
            response: ExplanationResponse = self._gemini.generate_structured(
                system_prompt=self._system_prompt,
                user_prompt=user_prompt,
                response_schema=ExplanationResponse,
            )
            return response
        except LLMException as exc:
            logger.error("explainer_generation_failed", error=str(exc))
            # Fallback for resiliency
            return ExplanationResponse(
                executive_summary="Explanation generation failed due to an LLM error.",
                detailed_explanation=f"Error details: {exc}",
                compliance_recommendation="MANUAL_REVIEW_REQUIRED",
                next_steps=["Review raw JSON data", "Check Gemini API connectivity"]
            )
