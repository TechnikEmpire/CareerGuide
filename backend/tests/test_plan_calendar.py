"""Tests for schedule-aware plan enrichment and ICS export."""

from __future__ import annotations

from datetime import date

from backend.app.services.generation.plan_calendar import build_plan_ics, finalize_career_plan
from backend.app.services.generation.schemas import CareerPlanRequest, CareerPlanStep, RetrievedChunk, StudyPreferences
from backend.app.services.retrieval.rag_pipeline import RetrievalContext


def _request() -> CareerPlanRequest:
    return CareerPlanRequest(
        user_id="demo-user",
        goal="Build a transition plan into project management",
        target_role="Project Manager",
        study_preferences=StudyPreferences(
            study_start_date=date(2026, 4, 6),
            preferred_study_time="evening",
            study_frequency_per_week=3,
            session_duration_minutes=90,
            timezone="America/St_Johns",
        ),
    )


def _retrieval_context() -> RetrievalContext:
    return RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="occupation-1",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/occupation",
                title="project manager",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: project manager.\n"
                    "Description (EN): Coordinate project delivery and stakeholder communication.\n"
                    "Essential skills (EN): risk management, stakeholder communication, resource planning, conflict resolution."
                ),
                score=0.93,
            )
        ],
        memory_summary="No memory.",
    )


def test_finalize_career_plan_adds_schedule_and_grounded_step_metadata() -> None:
    response = finalize_career_plan(
        request=_request(),
        retrieval_context=_retrieval_context(),
        goal="Build a transition plan into project management",
        target_role="Project Manager",
        steps=[
            CareerPlanStep(title="Clarify the target role", description="Choose the closest version of the role."),
            CareerPlanStep(title="Map current skills", description="Compare your background to the role."),
            CareerPlanStep(title="Build practice evidence", description="Complete a small work sample."),
        ],
    )

    assert response.workload_level == "medium"
    assert response.estimated_weeks >= 1
    assert response.study_preferences.preferred_study_time == "evening"
    assert response.calendar_events
    assert response.calendar_events[0].starts_at.startswith("2026-04-06T19:00:00")
    assert response.calendar_events[0].session_index == 1
    assert response.calendar_events[0].total_sessions >= 1
    assert any(
        skill in response.steps[1].description.lower()
        for skill in ("resource planning", "conflict resolution", "risk management")
    )
    assert response.steps[1].focus_skills


def test_build_plan_ics_serializes_calendar_events() -> None:
    response = finalize_career_plan(
        request=_request(),
        retrieval_context=_retrieval_context(),
        goal="Build a transition plan into project management",
        target_role="Project Manager",
        steps=[
            CareerPlanStep(title="Clarify the target role", description="Choose the closest version of the role."),
            CareerPlanStep(title="Map current skills", description="Compare your background to the role."),
        ],
    )

    ics_text = build_plan_ics(response, user_id="demo-user")

    assert "BEGIN:VCALENDAR" in ics_text
    assert "BEGIN:VEVENT" in ics_text
    assert "SUMMARY:Project Manager" in ics_text
    assert "TZID=America/St_Johns" in ics_text


def test_finalize_career_plan_keeps_data_roles_compact_and_filters_low_signal_topics() -> None:
    request = CareerPlanRequest(
        user_id="demo-user",
        goal="Build a realistic transition plan into data analytics in 6 months",
        target_role="Data Analyst",
        study_preferences=StudyPreferences(
            study_start_date=date(2026, 4, 6),
            preferred_study_time="evening",
            study_frequency_per_week=3,
            session_duration_minutes=90,
            timezone="America/St_Johns",
        ),
    )
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="occupation-1",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/occupation",
                title="data analyst",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: data analyst.\n"
                    "Description (EN): Data analysts import, inspect, clean, transform, validate, model, or interpret collections of data with regard to the business goals of the company. "
                    "They ensure that the data sources and repositories provide consistent and reliable data. They might prepare reports in the form of visualisations such as graphs, charts, and dashboards.\n"
                    "Essential skills (EN): digital data processing, information structure, business intelligence, data mining, documentation types, visual presentation techniques, data engineering, data visualisation software."
                ),
                score=0.93,
            )
        ],
        memory_summary="No memory.",
    )

    response = finalize_career_plan(
        request=request,
        retrieval_context=retrieval_context,
        goal=request.goal,
        target_role=request.target_role,
        steps=[
            CareerPlanStep(title="Clarify the target role", description="Use the current evidence to pin down the role."),
            CareerPlanStep(title="Map current skills", description="Compare your existing background against the role."),
            CareerPlanStep(title="Build practice evidence", description="Choose one compact project."),
            CareerPlanStep(title="Turn the work into proof", description="Write up what you built."),
        ],
    )

    assert response.workload_level == "medium"
    assert "they ensure" not in response.steps[0].description.lower()
    assert len(response.steps[0].description.split()) < 40
    assert "information structure" not in response.steps[1].description.lower()
    assert "documentation types" not in response.steps[2].description.lower()
    all_focus_topics = {
        topic.casefold()
        for step in response.steps
        for topic in step.focus_skills
    }
    assert "business intelligence" in all_focus_topics
    assert "data mining" in all_focus_topics
    assert "sql" in all_focus_topics
    assert "python with pandas" in all_focus_topics
    assert any("SQL" in event.description for event in response.calendar_events)
    clarify_events = [event for event in response.calendar_events if event.step_index == 1]
    assert len(clarify_events) >= 2
    assert clarify_events[0].description != clarify_events[1].description


def test_finalize_career_plan_adds_specific_software_study_topics() -> None:
    request = CareerPlanRequest(
        user_id="demo-user",
        goal="Build a study path into web development",
        target_role="Web Developer",
        study_preferences=StudyPreferences(
            study_start_date=date(2026, 4, 6),
            preferred_study_time="evening",
            study_frequency_per_week=3,
            session_duration_minutes=90,
            timezone="America/St_Johns",
        ),
    )
    retrieval_context = RetrievalContext(
        chunks=[
            RetrievedChunk(
                chunk_id="occupation-1",
                chunk_type="occupation",
                source_name="ESCO",
                source_url="http://example.com/occupation",
                title="web developer",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: web developer.\n"
                    "Description (EN): Web developers create and maintain web applications.\n"
                    "Essential skills (EN): software design, debug software, develop software prototype."
                ),
                score=0.93,
            )
        ],
        memory_summary="No memory.",
    )

    response = finalize_career_plan(
        request=request,
        retrieval_context=retrieval_context,
        goal=request.goal,
        target_role=request.target_role,
        steps=[
            CareerPlanStep(title="Clarify the target role", description="Choose the closest version of the role."),
            CareerPlanStep(title="Map current skills", description="Compare your background to the role."),
            CareerPlanStep(title="Build practice evidence", description="Complete a small work sample."),
        ],
    )

    all_focus_topics = {
        topic.casefold()
        for step in response.steps
        for topic in step.focus_skills
    }
    assert "javascript" in all_focus_topics
    assert "react" in all_focus_topics
    assert "git" in all_focus_topics
    assert any("JavaScript" in event.description or "React" in event.description for event in response.calendar_events)
