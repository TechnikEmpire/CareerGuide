"""Shared Pydantic schemas used across API and service layers."""

from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import uuid4

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
    question: str = Field(min_length=1)
    current_plan: "CareerPlanResponse | None" = None
    conversation_context: list["ChatContextTurn"] = Field(default_factory=list, max_length=8)
    pending_plan_handoff: "PlanHandoffSuggestion | None" = None


class AnswerResponse(BaseModel):
    answer: str
    citations: list[RetrievedChunk]
    prompt_preview: str
    memory_summary: str
    response_kind: str = "answer"
    plan_update: "PlanUpdateSuggestion | None" = None
    plan_handoff: "PlanHandoffSuggestion | None" = None


class ChatContextTurn(BaseModel):
    role: Literal["assistant", "user"]
    text: str = Field(min_length=1, max_length=1000)


class PlanHandoffSuggestion(BaseModel):
    status: Literal["offered", "accepted", "declined"]
    target_role: str
    goal: str
    source: Literal["supported_role_match"] = "supported_role_match"


class CareerPlanRequest(BaseModel):
    user_id: str = "demo-user"
    goal: str = Field(min_length=3)
    target_role: str
    study_preferences: "StudyPreferences" = Field(default_factory=lambda: StudyPreferences())


class StudyPreferences(BaseModel):
    study_start_date: date | None = None
    preferred_study_time: str = "evening"
    study_frequency_per_week: int = Field(default=3, ge=1, le=7)
    session_duration_minutes: int = Field(default=90, ge=30, le=240)
    timezone: str = "UTC"


class CareerPlanStep(BaseModel):
    title: str
    description: str
    focus_skills: list[str] = Field(default_factory=list)
    grounded_detail: str | None = None
    estimated_hours: float | None = Field(default=None, ge=0.0)


class CareerPlanCalendarEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: Literal["study", "break"] = "study"
    title: str
    description: str
    starts_at: str
    ends_at: str
    week_index: int = Field(ge=1)
    step_index: int = Field(ge=1)
    session_index: int = Field(ge=1)
    total_sessions: int = Field(ge=1)


class CareerPlanResponse(BaseModel):
    goal: str
    target_role: str
    workload_level: str = "medium"
    estimated_weeks: int = Field(default=1, ge=1)
    study_preferences: StudyPreferences = Field(default_factory=lambda: StudyPreferences())
    steps: list[CareerPlanStep]
    calendar_events: list[CareerPlanCalendarEvent] = Field(default_factory=list)
    citations: list[RetrievedChunk]


class PlanUpdateSuggestion(BaseModel):
    kind: Literal["relax_schedule", "schedule_preferences", "add_focus_topic"]
    summary: str
    updated_plan: CareerPlanResponse


class CareerPlanExportRequest(BaseModel):
    user_id: str = "demo-user"
    plan: CareerPlanResponse


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
