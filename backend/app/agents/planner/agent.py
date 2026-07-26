"""
Agent: PlannerAgent

Receives a natural language query and returns a validated ExecutionPlan.

Responsibilities (strictly limited):
- Load the system prompt from prompts/planner.md
- Pass the query to GeminiService with structured JSON output enforcement
- Validate the returned plan via ExecutionPlanValidator
- Return the validated ExecutionPlan to the Supervisor

The Planner NEVER executes tools.
The Planner NEVER accesses the database.
The Planner NEVER contains business logic.
All retry and Gemini concerns live in GeminiService.
"""
from pathlib import Path

from app.core.exceptions import PlannerException, ValidationException
from app.interfaces.agents import BaseAgent
from app.logging.logger import get_logger
from app.schemas.execution_plan import ExecutionPlan
from app.services.gemini import GeminiService
from app.validators.execution_plan import ExecutionPlanValidator

logger = get_logger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "planner.md"


class PlannerAgent(BaseAgent):
    """
    AI Planner Agent — translates natural language into a typed ExecutionPlan.

    Injected with GeminiService and ExecutionPlanValidator so it can be
    tested in isolation without requiring a live Gemini API or database.
    """

    def __init__(
        self,
        gemini: GeminiService,
        validator: ExecutionPlanValidator,
    ) -> None:
        self._gemini = gemini
        self._validator = validator
        self._system_prompt = self._load_prompt()

    @property
    def name(self) -> str:
        return "PlannerAgent"

    def _load_prompt(self) -> str:
        """
        Loads the system prompt from prompts/planner.md.

        Raises PlannerException if the file is missing — fail loudly at
        startup rather than silently using an empty prompt.
        """
        if not _PROMPT_PATH.exists():
            raise PlannerException(
                f"Planner prompt file not found at '{_PROMPT_PATH}'. "
                "Ensure prompts/planner.md exists in the backend directory."
            )
        content = _PROMPT_PATH.read_text(encoding="utf-8").strip()
        if not content:
            raise PlannerException("Planner prompt file is empty.")
        logger.info("planner_prompt_loaded", path=str(_PROMPT_PATH))
        return content

    async def process(self, query: str) -> ExecutionPlan:
        """
        Produces a validated ExecutionPlan for the given user query.

        Flow:
            1. Send query to Gemini with structured output schema.
            2. Gemini returns a JSON payload parsed into ExecutionPlan.
            3. ExecutionPlanValidator checks tool names against the ToolRegistry.
            4. Return the plan to the Supervisor.

        Args:
            query: Natural language query from the compliance officer.

        Returns:
            A validated ExecutionPlan instance.

        Raises:
            PlannerException: If Gemini fails to produce a valid plan.
            ValidationException: If the plan fails registry validation.
        """
        logger.info("planner_processing_query", query=query[:120])

        try:
            plan: ExecutionPlan = self._gemini.generate_structured(
                system_prompt=self._system_prompt,
                user_prompt=query,
                response_schema=ExecutionPlan,
            )
        except Exception as exc:
            raise PlannerException(
                f"Planner failed to generate an execution plan: {exc}"
            ) from exc

        logger.info(
            "planner_plan_generated",
            intent=plan.intent,
            tools=[t.value for t in plan.tools],
            confidence=plan.confidence,
        )

        # Validate against tool registry (raises ValidationException on failure)
        self._validator.validate(plan)

        logger.info(
            "planner_plan_validated",
            tool_count=len(plan.tools),
            intent=plan.intent,
        )
        return plan
