"""Tests for schedule-aware plan enrichment and ICS export."""

from __future__ import annotations

from datetime import date

from backend.app.services.generation.plan_adjustments import maybe_build_plan_update
from backend.app.services.generation.plan_calendar import build_plan_ics, finalize_career_plan
from backend.app.services.generation.schemas import CareerPlanRequest, CareerPlanStep, RetrievedChunk, StudyPreferences
from backend.app.services.generation.skill_enrichment import EnrichedSkill, SkillEnrichment
from backend.app.services.generation.study_cadence import estimate_study_cadence, extract_hours_per_week
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


def _fake_enrichment(role_label: str, skill_names: list[str]) -> SkillEnrichment:
    return SkillEnrichment(
        role_label=role_label,
        language_code="en",
        used_model=True,
        skills=[
            EnrichedSkill(
                name=name,
                rationale=f"Fake model output for {role_label}.",
                study_order=index,
                effort_level="medium",
                practice_tasks=[f"Practice {name} with a small role-relevant exercise"],
            )
            for index, name in enumerate(skill_names, start=1)
        ],
    )


def test_study_cadence_uses_explicit_low_hour_availability() -> None:
    estimate = estimate_study_cadence(
        role_label="Data Analyst",
        focus_topics=["SQL", "Python with pandas", "data visualization", "basic statistics"],
        workload_level="medium",
        availability_text="I can study 5 hours per week.",
    )

    assert extract_hours_per_week("Я могу учиться 5 часов в неделю.") == 5
    assert estimate.hours_per_week == 5
    assert estimate.estimated_weeks >= 5
    assert estimate.topic_efforts[0].topic == "SQL"
    assert estimate.topic_efforts[0].estimated_hours >= 4


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
    assert response.calendar_events[0].event_id.startswith("evt-")
    assert response.calendar_events[0].event_type == "study"
    assert response.calendar_events[0].starts_at.startswith("2026-04-06T19:00:00")
    assert response.calendar_events[0].session_index == 1
    assert response.calendar_events[0].total_sessions >= 1
    all_step_text = " ".join(step.description.lower() for step in response.steps)
    assert any(
        skill in all_step_text
        for skill in ("stakeholder communication", "risk management", "resource planning")
    )
    assert response.steps[1].focus_skills

    repeated_response = finalize_career_plan(
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
    assert repeated_response.calendar_events[0].event_id == response.calendar_events[0].event_id


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
        skill_enrichment=_fake_enrichment(
            "data analyst",
            ["SQL", "Python with pandas", "data visualization", "basic statistics"],
        ),
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
    assert "business intelligence" not in all_focus_topics
    assert "data engineering" not in all_focus_topics
    assert "sql" in all_focus_topics
    assert "python with pandas" in all_focus_topics
    assert sum(step.estimated_hours or 0 for step in response.steps) >= 24
    assert response.estimated_weeks >= 6
    assert any("SQL" in event.description for event in response.calendar_events)
    clarify_events = [event for event in response.calendar_events if event.step_index == 1]
    assert len(clarify_events) >= 2
    assert clarify_events[0].description != clarify_events[1].description


def test_finalize_career_plan_aligns_specific_titles_focus_and_sessions() -> None:
    request = CareerPlanRequest(
        user_id="demo-user",
        goal="Build a realistic transition study plan for data analyst",
        target_role="data analyst",
        study_preferences=StudyPreferences(
            study_start_date=date(2026, 5, 4),
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
                    "Description (EN): Data analysts import, inspect, clean, transform, validate, model, or interpret collections of data.\n"
                    "Essential skills (EN): business intelligence, business process modelling, data analytics, data engineering."
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
            CareerPlanStep(title="Master SQL and Data Cleaning Techniques", description="Learn core query and cleaning work."),
            CareerPlanStep(title="Develop Python Skills with Pandas", description="Practice Python data workflows."),
            CareerPlanStep(title="Learn Data Visualization and Dashboard Storytelling", description="Create visual summaries."),
        ],
        skill_enrichment=_fake_enrichment(
            "data analyst",
            ["SQL", "data cleaning", "Python with pandas", "data visualization", "dashboard storytelling"],
        ),
    )

    first_step = response.steps[0]
    assert "SQL" in first_step.focus_skills
    assert "data cleaning" in first_step.focus_skills
    assert "business intelligence" not in first_step.focus_skills
    assert "Pin down which version" not in first_step.description
    assert "SQL" in first_step.description

    second_step = response.steps[1]
    assert "Python with pandas" in second_step.focus_skills
    assert "Python" in second_step.description

    third_step = response.steps[2]
    assert "data visualization" in third_step.focus_skills
    assert "dashboard storytelling" in third_step.focus_skills

    first_event = response.calendar_events[0]
    assert first_event.title == "data analyst: Master SQL and Data Cleaning Techniques"
    assert "Review the role shape" not in first_event.description
    assert "SQL" in first_event.description
    assert "data cleaning" in first_event.description


def test_finalize_career_plan_does_not_promote_abstract_esco_labels_without_model_enrichment() -> None:
    request = CareerPlanRequest(
        user_id="demo-user",
        goal="Build a realistic transition study plan for data analyst",
        target_role="data analyst",
        study_preferences=StudyPreferences(
            study_start_date=date(2026, 5, 4),
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
                    "Description (EN): Data analysts inspect and interpret collections of data.\n"
                    "Essential skills (EN): business intelligence, data analytics."
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
            CareerPlanStep(title="Build practice evidence", description="Complete a small work sample."),
        ],
    )

    all_focus_topics = {
        topic.casefold()
        for step in response.steps
        for topic in step.focus_skills
    }
    assert "business intelligence" not in all_focus_topics
    assert "data analytics" not in all_focus_topics
    assert "sql" not in all_focus_topics
    assert "python with pandas" not in all_focus_topics


def test_finalize_career_plan_uses_model_enriched_software_study_topics() -> None:
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
        skill_enrichment=_fake_enrichment(
            "web developer",
            ["JavaScript", "React", "Git"],
        ),
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


def test_finalize_career_plan_preserves_concrete_model_steps_and_hour_proportions() -> None:
    request = CareerPlanRequest(
        user_id="demo-user",
        goal="Build a study path into UX design",
        target_role="UX Designer",
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
                title="ux designer",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: UX designer.\n"
                    "Description (EN): UX designers improve interaction flows and test digital product experiences.\n"
                    "Essential skills (EN): user interface design, usability testing, prototype development."
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
            CareerPlanStep(
                title="Wireframe critique practice",
                description="Review two wireframes and write three concrete interaction improvements.",
                estimated_hours=2,
            ),
            CareerPlanStep(
                title="Usability interview notes",
                description="Draft interview questions, run one short practice interview, and summarize patterns.",
                estimated_hours=6,
            ),
        ],
        skill_enrichment=_fake_enrichment(
            "UX designer",
            ["Wireframe critique", "Usability interview notes"],
        ),
    )

    assert response.steps[0].description == "Review two wireframes and write three concrete interaction improvements."
    assert response.steps[1].description == (
        "Draft interview questions, run one short practice interview, and summarize patterns."
    )
    assert response.steps[1].estimated_hours > response.steps[0].estimated_hours * 2
    assert sum(step.estimated_hours or 0 for step in response.steps) >= 14
    visible_text = " ".join(step.description for step in response.steps).casefold()
    assert "work directly on" not in visible_text
    assert "tie the practice back" not in visible_text
    assert "finish with a small checkable result" not in visible_text


def test_calendar_sessions_use_practice_tasks_without_repeated_generic_closing() -> None:
    request = CareerPlanRequest(
        user_id="demo-user",
        goal="Build a study path into portfolio-focused design work",
        target_role="Design Assistant",
        study_preferences=StudyPreferences(
            study_start_date=date(2026, 4, 6),
            preferred_study_time="evening",
            study_frequency_per_week=3,
            session_duration_minutes=60,
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
                title="design assistant",
                text=(
                    "ESCO concept kind: occupation.\n"
                    "English label: design assistant.\n"
                    "Description (EN): Design assistants support visual and product design work.\n"
                    "Essential skills (EN): design drawings, prototype development."
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
            CareerPlanStep(
                title="Portfolio case study",
                description="Create one case-study artifact that shows a design decision.",
            ),
        ],
        skill_enrichment=_fake_enrichment("design assistant", ["Portfolio case study"]),
    )

    first_descriptions = [event.description for event in response.calendar_events[:4]]
    assert len(set(first_descriptions)) == len(first_descriptions)
    assert all("Portfolio case study" in description for description in first_descriptions)
    assert all("Briefly summarize" not in description for description in first_descriptions)


def test_plan_adjustment_relaxes_schedule_and_adds_breaks() -> None:
    plan = finalize_career_plan(
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

    update = maybe_build_plan_update("I am overwhelmed and close to burnout. Please relax the schedule.", plan)

    assert update is not None
    assert update.kind == "relax_schedule"
    assert update.updated_plan.workload_level == "low"
    assert update.updated_plan.study_preferences.study_frequency_per_week == 2
    assert update.updated_plan.study_preferences.session_duration_minutes == 60
    assert any(event.event_type == "break" for event in update.updated_plan.calendar_events)
    assert update.updated_plan.estimated_weeks >= plan.estimated_weeks


def test_plan_adjustment_updates_schedule_preferences() -> None:
    plan = finalize_career_plan(
        request=_request(),
        retrieval_context=_retrieval_context(),
        goal="Build a transition plan into project management",
        target_role="Project Manager",
        steps=[
            CareerPlanStep(title="Clarify the target role", description="Choose the closest version of the role."),
            CareerPlanStep(title="Map current skills", description="Compare your background to the role."),
        ],
    )

    update = maybe_build_plan_update("Please make it 2 sessions per week in the morning.", plan)

    assert update is not None
    assert update.kind == "schedule_preferences"
    assert update.updated_plan.study_preferences.study_frequency_per_week == 2
    assert update.updated_plan.study_preferences.preferred_study_time == "morning"
    assert update.updated_plan.calendar_events[0].starts_at.startswith("2026-04-07T08:00:00")


def test_plan_adjustment_adds_focus_topic_to_events() -> None:
    plan = finalize_career_plan(
        request=_request(),
        retrieval_context=_retrieval_context(),
        goal="Build a transition plan into project management",
        target_role="Project Manager",
        steps=[
            CareerPlanStep(title="Clarify the target role", description="Choose the closest version of the role."),
            CareerPlanStep(title="Build practice evidence", description="Complete a small work sample."),
        ],
    )

    update = maybe_build_plan_update("Add more SQL practice to the plan.", plan)

    assert update is not None
    assert update.kind == "add_focus_topic"
    assert any("SQL" in step.focus_skills for step in update.updated_plan.steps)
    assert any("SQL" in event.description for event in update.updated_plan.calendar_events)
