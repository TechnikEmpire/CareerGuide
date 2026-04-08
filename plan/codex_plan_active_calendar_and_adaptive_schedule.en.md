# Codex Plan: Active Calendar and Adaptive Scheduling

Last updated: 2026-04-07

## Status of This Document

This is an **active post-v1 extension plan**, not a description of current live
frontend/backend behavior.

The current live system can still:

- build a structured plan
- show a schedule preview inside the plan artifact
- export `.ics`

But it does **not yet** keep a backend-canonical active calendar per user, and
it does not yet let the user accept or reject AI-generated rescheduling
proposals.

## Extension Goal

The extension must turn the current plan preview into a real active calendar
that:

- belongs to the active user
- is stored in the backend and in SQLite
- is displayed inside the web UI
- can be edited manually by the user
- can receive wellbeing-driven proposal diffs from the assistant
- remains exportable as `.ics` from persisted server-side state

## Locked Decisions

- The active calendar becomes backend-canonical per user.
- Frontend localStorage remains only a cache/fallback layer.
- Plans and calendars are separated:
  - a generated plan may exist as a draft
  - an active calendar appears only after explicit activation
- Only one active plan is allowed per user at any given time.
- The assistant does not modify the calendar autonomously.
- Any wellbeing-driven schedule change is first expressed as a proposal diff.
- The user must explicitly accept or reject the proposal.
- The calendar widget is fixed as `@fullcalendar/react`.
- The graphing library is fixed as `Recharts`.
- The event model is fixed in advance:
  - kinds: `study|wellbeing|checkpoint|recovery`
  - statuses: `scheduled|completed|skipped|cancelled`
- Timezone ownership remains with the backend.
- `.ics` export must later come from the persisted active calendar, not from a
  frontend snapshot.
- The rescheduling priority order is fixed as:
  1. reduce `session_duration`
  2. lower `study_frequency_per_week`
  3. insert `wellbeing|recovery` blocks
  4. only then extend the timeline
- The existing `POST /career/plan/export-ics` later remains a compatibility
  wrapper for one release cycle.

## Target Implementation by Stage

### Stage 1. Canonical Calendar Persistence

Stage goal:

- move plans and schedules from a local-only surface into inspectable
  backend-owned state

Planned new database tables:

- `career_plan_snapshots`
- `calendar_events`
- `calendar_event_history`
- `schedule_proposals`

`career_plan_snapshots` should later store:

- `id`
- `user_id`
- `goal`
- `target_role`
- `plan_json`
- `study_preferences_json`
- `status` with `draft|active|archived`
- `created_at`
- `activated_at`

`calendar_events` should later store:

- `id`
- `plan_id`
- `user_id`
- `kind`
- `status`
- `title`
- `description`
- `starts_at`
- `ends_at`
- `timezone`
- `step_index`
- `session_index`
- `total_sessions`
- `origin` with `plan|proposal|manual`

`calendar_event_history` should later store:

- `id`
- `event_id`
- `user_id`
- `action`
- `payload_json`
- `created_at`

`schedule_proposals` should later store:

- `id`
- `user_id`
- `plan_id`
- `trigger`
- `risk_band`
- `summary`
- `proposal_json`
- `status` with `pending|accepted|rejected|expired`
- `created_at`
- `decided_at`

Planned new modules later:

- `backend/app/api/calendar.py`
- `backend/app/services/calendar/__init__.py`
- `backend/app/services/calendar/plan_store.py`
- `backend/app/services/calendar/event_store.py`
- `backend/app/services/calendar/proposals.py`
- `backend/app/services/calendar/ics_export.py`

The key persistence rules are:

- a generated plan is first saved as `draft`
- only activation makes it `active`
- the previous active plan moves to `archived` during a new activation
- future uncompleted events from the old active plan become `cancelled`
- completed historical events are preserved for auditability

Stage acceptance criteria:

- there is inspectable active calendar state in SQLite
- the frontend is no longer the only owner of the saved plan
- the lifecycle `draft -> active -> archived` is fixed deterministically

### Stage 2. Active Plan Activation Flow

Stage goal:

- separate “the LLM generated a plan” from “the user actually accepted this plan
  as the working schedule”

The later API behavior is fixed as follows:

- `POST /career/plan`
  - still builds a grounded plan response
  - does not make it active automatically
- `POST /career/plan/activate`
  - accepts the selected plan
  - creates a `career_plan_snapshot`
  - materializes `calendar_events`
  - returns `ActivePlanResponse`
- `GET /career/plan/active`
  - returns the current active plan for the user

`ActivePlanResponse` must later include:

- `plan_id`
- `goal`
- `target_role`
- `workload_level`
- `estimated_weeks`
- `study_preferences`
- `calendar_events`
- `latest_proposal`
- `activated_at`

Activation rules are fixed:

- activation is an explicit user action
- only one active plan may exist per user
- active calendar generation is a backend-owned reuse of the plan calendar logic
- plan activation must preserve original grounded citations inside the snapshot
  JSON

Stage acceptance criteria:

- generated plans and active plans are no longer conceptually mixed
- the user can reload the active plan from any browser session
- the activation path does not depend on localStorage

### Stage 3. Calendar UI and Event Model

Stage goal:

- show the active schedule as a first-class UI surface
- preserve visual congruence with the current custom React + CSS shell

Later dependency additions are fixed:

- `@fullcalendar/react`
- `@fullcalendar/core`
- `@fullcalendar/daygrid`
- `@fullcalendar/timegrid`
- `@fullcalendar/list`
- `@fullcalendar/interaction`
- `recharts`
- `react-is` only if required by chart version alignment

Why `FullCalendar`:

- mature React integration
- MIT license
- built-in month, week, and list views
- supports event editing and drag interactions
- does not force a second UI framework into the app

Why `Recharts`:

- React-first component model
- MIT license
- flexible enough for the current dark visual system
- suitable for compact wellbeing history graphs without excessive infra cost

The later frontend surface is fixed like this:

- a top-level `calendar` workspace view is added
- the `plan` view keeps draft generation and activation actions
- the `calendar` view becomes the home of:
  - the active plan summary
  - the FullCalendar surface
  - the wellbeing trend graph
  - the pending proposal review card
  - the event detail drawer

Calendar interaction rules:

- drag/drop and resize are allowed for `scheduled` events
- `completed` and `skipped` are changed through explicit action buttons, not
  drag gestures
- manual edits go through backend `PATCH`
- each edit writes an audit history entry

Visual design constraints:

- reuse the current CSS variables and dark theme
- do not add a component-library skin over the current look
- the wellbeing graph should align with the current accent palette
- calendar badges for `study|wellbeing|checkpoint|recovery` must be clearly
  distinguishable but not harsh

Stage acceptance criteria:

- the active calendar is available as a separate UI surface
- manual event edits round-trip through the backend
- the wellbeing graph does not visually clash with the current shell

### Stage 4. Proposal-Based Rescheduling

Stage goal:

- connect wellbeing signals to scheduling without losing user agency

The new proposal lifecycle must later be:

1. the wellbeing system detects an `amber|red` support condition
2. the calendar service builds a proposal diff, not a direct mutation
3. the proposal is stored as `pending`
4. the frontend shows a summary, a rationale, and an event preview
5. the user accepts or rejects it
6. the backend applies the diff only after acceptance

New public schemas later:

- `CalendarEventUpdateRequest`
- `ScheduleProposalResponse`

`CalendarEventUpdateRequest` later fields:

- `starts_at`
- `ends_at`
- `status`
- `title`
- `description`

`ScheduleProposalResponse` later fields:

- `proposal_id`
- `plan_id`
- `risk_band`
- `reason_summary`
- `changes`
- `preview_events`
- `created_at`

Proposal triggers may later include:

- an explicit `WHO-5` check-in
- a passive chat signal with `amber|red`
- repeated skipped sessions
- a manual user request to “make the plan lighter”

Only one pending proposal is allowed per active plan.

If a new trigger fires while a `pending` proposal already exists:

- the old proposal becomes `expired`
- the new proposal becomes the only active review item

Proposal change types are fixed:

- `shorten_session`
- `reduce_weekly_frequency`
- `insert_recovery_block`
- `insert_wellbeing_block`
- `extend_timeline`

The proposal builder must follow the locked priority order:

1. shorten session duration
2. reduce weekly frequency
3. insert recovery and wellbeing tasks
4. extend the total timeline only if the first three actions do not remove the
   overload risk

Stage acceptance criteria:

- wellbeing never mutates the plan silently
- each proposal has a human-readable rationale
- proposal acceptance produces a traceable history entry

### Stage 5. ICS Parity and Export Ownership

Stage goal:

- make `.ics` export an honest reflection of the active calendar rather than a
  frontend approximation

Later canonical route:

- `GET /calendar/export-ics`

Backward compatibility route for one release cycle:

- `POST /career/plan/export-ics`

Export rules are fixed as follows:

- active export always serializes persisted `calendar_events`
- `cancelled` events are excluded from `.ics`
- `skipped` events are excluded from `.ics`
- `scheduled` and `completed` events are exported
- timezone is taken from persisted event data
- title and description come from persisted event state, not from the original
  unsynced draft

Compatibility wrapper behavior later:

- if an active persisted calendar exists, the wrapper delegates to the same
  export serializer
- if the user only has a transient draft plan, the wrapper may still build a
  temporary export for compatibility
- after one release cycle, the docs should move user guidance to
  `GET /calendar/export-ics`

Stage acceptance criteria:

- exported `.ics` matches the visible active calendar
- export no longer depends on frontend-local saved plan state
- compatibility behavior is explicit and temporary

### Stage 6. Frontend Flows and UX States

Stage goal:

- guide the user through generation, activation, daily use, manual edits, and
  proposal review without UX ambiguity

The later frontend flow is fixed as follows:

1. the user generates a plan in the `plan` view
2. the frontend shows the draft plan with an activation CTA
3. the user activates the plan
4. the frontend switches to the `calendar` view or offers direct navigation
5. the calendar view shows:
   - the current active schedule
   - manual edit affordances
   - the wellbeing trend graph
   - the pending proposal card if present
6. the chat view may show a lightweight banner when a new schedule proposal
   exists
7. the user can accept or reject the proposal from the chat or calendar view

The later localStorage policy:

- localStorage may cache:
  - the last selected month or view mode
  - the last fetched active calendar snapshot
  - UI-only panel state
- localStorage must not remain canonical for:
  - active plan content
  - event statuses
  - accepted proposals

Later RU-first UI copy updates will be required in:

- `frontend/src/config/ui.ru.ts`
- `frontend/src/config/ui.en.ts`
- `frontend/src/config/ui.types.ts`

Stage acceptance criteria:

- the user always understands whether they are looking at a draft plan or an
  active calendar
- proposal review is available from at least one primary flow and one secondary
  flow
- local cache does not create a conflicting truth against the backend

### Stage 7. Regression, Documentation, and Release Criteria

Stage goal:

- make the active calendar extension inspectable, regression-safe, and easy to
  defend in a demo

Later routes to implement:

- `GET /career/plan/active`
- `POST /career/plan/activate`
- `GET /calendar/active`
- `PATCH /calendar/events/{event_id}`
- `POST /calendar/proposals/{proposal_id}/accept`
- `POST /calendar/proposals/{proposal_id}/reject`
- `GET /calendar/export-ics`

Later tests must include:

- the activation flow
- one-active-plan-per-user enforcement
- manual event edits
- event overlap handling
- proposal accept/reject
- timezone preservation
- `.ics` parity with persisted events
- FullCalendar rendering smoke coverage
- Recharts wellbeing graph rendering smoke coverage

Planned later test files:

- `backend/tests/test_active_plan_api.py`
- `backend/tests/test_calendar_events.py`
- `backend/tests/test_schedule_proposals.py`
- `backend/tests/test_calendar_export.py`
- `frontend/src/App.test.tsx`
- new frontend tests for calendar and proposal states

Documentation updates required at implementation time:

- `docs/DECISIONS.en.md`
- `docs/STATUS.en.md`
- `docs/ROADMAP.en.md`
- `docs/STUDENT_MANUAL.en.md`
- `docs/SETUP.en.md` if new frontend dependencies or workflows are added

Release criteria for this extension:

1. the active plan persists on the backend
2. one active plan per user is enforced
3. the FullCalendar view renders persisted events correctly
4. manual edits survive reload and cross-session use
5. the wellbeing trend graph renders real backend data
6. proposals are reviewable and never auto-applied
7. `.ics` export matches persisted event state

## Explicitly Out of Scope for This Stage

- autonomous rescheduling without confirmation
- multi-user shared calendars
- direct Google Calendar or Outlook sync
- external notifications or reminder infrastructure
- replacing the existing plan-generation endpoint with a frontend-only planner

## External References

- FullCalendar React docs
  - <https://fullcalendar.io/docs/react>
- Recharts GitHub
  - <https://github.com/recharts/recharts>
- Recharts docs
  - <https://recharts.github.io/>

## Practical Outcome

This plan moves scheduling from the current preview mode into a backend-owned
active calendar system with user-approved adaptive changes.

It intentionally depends on the wellbeing signal layer described in:

- `codex_plan_wellbeing_rag_and_signals.en.md`

Until this plan is implemented, the live system still remains on the current
schedule-preview + `.ics` export model.
