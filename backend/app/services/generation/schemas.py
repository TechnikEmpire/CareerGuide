"""Shared Pydantic schemas used across API and service layers."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    chunk_id: str | None = None
    chunk_type: str | None = None
    source_name: str
    source_url: str
    title: str
    text: str
    score: float
    dense_score: float | None = None
    rerank_score: float | None = None


class AnswerRequest(BaseModel):
    user_id: str = "demo-user"
    question: str = Field(min_length=3)


class AnswerResponse(BaseModel):
    answer: str
    citations: list[RetrievedChunk]
    prompt_preview: str
    memory_summary: str
    response_kind: str = "answer"


class CareerPlanRequest(BaseModel):
    user_id: str = "demo-user"
    goal: str = Field(min_length=3)
    target_role: str


class CareerPlanStep(BaseModel):
    title: str
    description: str


class CareerPlanResponse(BaseModel):
    goal: str
    target_role: str
    steps: list[CareerPlanStep]
    citations: list[RetrievedChunk]


class MemoryItemPayload(BaseModel):
    id: str
    user_id: str
    text: str
    category: str
    importance: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)


class MemoryUpsertRequest(BaseModel):
    item: MemoryItemPayload


class EvalScenario(BaseModel):
    id: str
    language: str = Field(pattern="^(en|ru)$")
    scenario_group: str
    question: str
    expected_behavior: str


class EvalRunRequest(BaseModel):
    scenarios: list[EvalScenario]


class EvalRunResponse(BaseModel):
    scenario_count: int
    baseline_names: list[str]
    status: str
    notes: str
