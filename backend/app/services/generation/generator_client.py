"""Generation client abstraction.

The real project will call a local `llama.cpp` server with the pinned GGUF
artifact. Until that runtime is wired in, the stub client returns transparent
structured responses so API and evaluation work can move forward.
"""

from __future__ import annotations

from backend.app.services.generation.schemas import (
    AnswerResponse,
    CareerPlanRequest,
    CareerPlanResponse,
    CareerPlanStep,
)
from backend.app.services.retrieval.rag_pipeline import RetrievalContext


class StubGeneratorClient:
    """Deterministic generation client used during the scaffold stage."""

    def generate_answer(
        self,
        question: str,
        prompt: str,
        retrieval_context: RetrievalContext,
        memory_items: list[object],
    ) -> AnswerResponse:
        """Build a transparent answer from retrieved evidence.

        The response makes the system behavior inspectable and stable while the
        real generator runtime is still pending.
        """

        supporting_titles = ", ".join(chunk.title for chunk in retrieval_context.chunks[:2])
        answer_text = (
            f"Scaffold answer for: {question}\n\n"
            f"Top supporting context: {supporting_titles or 'no sources yet'}.\n"
            f"Stored memory used: {len(memory_items)} item(s).\n"
            "This will later be replaced by a grounded llama.cpp generation step."
        )

        return AnswerResponse(
            answer=answer_text,
            citations=retrieval_context.chunks,
            prompt_preview=prompt,
            memory_summary=retrieval_context.memory_summary,
        )

    def generate_career_plan(
        self,
        request: CareerPlanRequest,
        retrieval_context: RetrievalContext,
    ) -> CareerPlanResponse:
        """Return a small structured plan placeholder."""

        return CareerPlanResponse(
            goal=request.goal,
            target_role=request.target_role,
            steps=[
                CareerPlanStep(
                    title="Clarify target role expectations",
                    description="Review retrieved career evidence and identify the most relevant role signals.",
                ),
                CareerPlanStep(
                    title="Map current skills to the target role",
                    description="List existing strengths, missing capabilities, and business-context gaps.",
                ),
                CareerPlanStep(
                    title="Create a 30-day learning slice",
                    description="Choose one compact learning sprint that can be defended and measured.",
                ),
            ],
            citations=retrieval_context.chunks,
        )
