# План Codex: active calendar и adaptive scheduling

Последнее обновление: 2026-04-07

## Статус этого документа

Это **активный план расширения после prototype v1**, а не описание текущего
live frontend/backend behavior.

Текущая live-система по-прежнему умеет:

- строить structured plan
- показывать schedule preview внутри plan artifact
- экспортировать `.ics`

Но она **еще не** хранит backend-canonical active calendar на пользователя и
еще не умеет принимать или отклонять AI-generated rescheduling proposals.

## Цель расширения

Расширение должно превратить текущий plan preview в настоящий active calendar,
который:

- принадлежит активному пользователю
- хранится в backend и SQLite
- отображается внутри web UI
- может быть вручную скорректирован пользователем
- может получать wellbeing-driven proposal diff от ассистента
- остается exportable в `.ics` из persisted server-side state

## Зафиксированные решения

- Active calendar становится backend-canonical per user.
- Frontend localStorage остается только cache/fallback layer.
- План и календарь разделяются:
  - generated plan может существовать как draft
  - active calendar появляется только после explicit activation
- На пользователя в каждый момент времени допускается только один active plan.
- Assistant не меняет календарь автономно.
- Любая wellbeing-driven перестройка расписания сначала оформляется как
  proposal diff.
- Пользователь обязан явно принять или отклонить proposal.
- Calendar widget фиксируется как `@fullcalendar/react`.
- Graphing library фиксируется как `Recharts`.
- Event model фиксируется заранее:
  - kinds: `study|wellbeing|checkpoint|recovery`
  - statuses: `scheduled|completed|skipped|cancelled`
- Timezone ownership остается у backend.
- `.ics` экспорт позже должен идти из persisted active calendar, а не из
  frontend snapshot.
- Rescheduling priority order фиксируется так:
  1. уменьшить `session_duration`
  2. снизить `study_frequency_per_week`
  3. вставить `wellbeing|recovery` blocks
  4. только потом расширить timeline
- Existing `POST /career/plan/export-ics` later остается compatibility-wrapper
  на один release-cycle.

## Целевая реализация по стадиям

### Stage 1. Canonical Calendar Persistence

Цель стадии:

- перевести план и расписание из local-only surface в inspectable backend-owned
  state

Новые planned database tables:

- `career_plan_snapshots`
- `calendar_events`
- `calendar_event_history`
- `schedule_proposals`

`career_plan_snapshots` later should store:

- `id`
- `user_id`
- `goal`
- `target_role`
- `plan_json`
- `study_preferences_json`
- `status` with `draft|active|archived`
- `created_at`
- `activated_at`

`calendar_events` later should store:

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

`calendar_event_history` later should store:

- `id`
- `event_id`
- `user_id`
- `action`
- `payload_json`
- `created_at`

`schedule_proposals` later should store:

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

Новые planned modules later:

- `backend/app/api/calendar.py`
- `backend/app/services/calendar/__init__.py`
- `backend/app/services/calendar/plan_store.py`
- `backend/app/services/calendar/event_store.py`
- `backend/app/services/calendar/proposals.py`
- `backend/app/services/calendar/ics_export.py`

Ключевые правила persistence:

- generated plan сначала сохраняется как `draft`
- только activation делает его `active`
- previous active plan при новой активации уходит в `archived`
- future uncompleted events старого active plan получают status `cancelled`
- completed historical events сохраняются для audit trail

Acceptance criteria стадии:

- в SQLite есть inspectable active calendar state
- фронтенд больше не является единственным владельцем saved plan
- lifecycle `draft -> active -> archived` зафиксирован детерминированно

### Stage 2. Active Plan Activation Flow

Цель стадии:

- отделить “LLM сгенерировал план” от “пользователь реально принял этот план как
  рабочее расписание”

Later API behavior is fixed as follows:

- `POST /career/plan`
  - по-прежнему строит grounded plan response
  - не делает его active автоматически
- `POST /career/plan/activate`
  - принимает selected plan
  - создает `career_plan_snapshot`
  - materialize-ит `calendar_events`
  - возвращает `ActivePlanResponse`
- `GET /career/plan/active`
  - возвращает текущий active plan для пользователя

`ActivePlanResponse` later must include:

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

- activation — explicit user action
- only one active plan may exist per user
- active calendar generation is backend-owned reuse of the plan calendar logic
- plan activation must preserve original grounded citations inside snapshot JSON

Acceptance criteria стадии:

- generated plan и active plan больше не смешиваются conceptually
- user может reload active plan с любого browser session
- activation path не зависит от localStorage

### Stage 3. Calendar UI and Event Model

Цель стадии:

- показать active schedule как first-class UI surface
- сохранить visual congruence с текущим custom React + CSS shell

Later dependency additions are fixed:

- `@fullcalendar/react`
- `@fullcalendar/core`
- `@fullcalendar/daygrid`
- `@fullcalendar/timegrid`
- `@fullcalendar/list`
- `@fullcalendar/interaction`
- `recharts`
- `react-is` only if required by charting version alignment

Почему `FullCalendar`:

- mature React integration
- MIT license
- built-in month/week/list views
- supports event editing and drag interactions
- не требует вводить второй UI-framework

Почему `Recharts`:

- React-first component model
- MIT license
- достаточно гибкий для current dark visual system
- подходит для compact wellbeing history graphs без избыточной infra-стоимости

Later frontend surface is fixed like this:

- top-level `calendar` workspace view is added
- `plan` view keeps draft generation and activation actions
- `calendar` view becomes the home of:
  - active plan summary
  - FullCalendar surface
  - wellbeing trend graph
  - pending proposal review card
  - event detail drawer

Calendar interaction rules:

- drag/drop и resize разрешены для `scheduled` events
- `completed` и `skipped` меняются explicit action buttons, а не drag gesture
- manual edits go through backend `PATCH`
- each edit writes audit history

Visual design constraints:

- использовать существующие CSS variables и dark theme
- не добавлять component library skin поверх current look
- wellbeing graph должен визуально совпадать с current accent palette
- calendar badges for `study|wellbeing|checkpoint|recovery` должны быть явно
  различимы, но не кислотны

Acceptance criteria стадии:

- active calendar доступен как отдельная UI surface
- manual event edits round-trip через backend
- wellbeing graph визуально не выбивается из текущего shell

### Stage 4. Proposal-Based Rescheduling

Цель стадии:

- связать wellbeing signals с расписанием без потери user agency

Новый proposal lifecycle later must be:

1. wellbeing system detects `amber|red` support condition
2. calendar service builds proposal diff, not direct mutation
3. proposal is stored as `pending`
4. frontend shows summary, rationale, and event preview
5. user accepts or rejects
6. backend applies diff only after acceptance

Новые public schemas later:

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

Proposal triggers later may include:

- explicit `WHO-5` check-in
- passive chat signal with `amber|red`
- repeated skipped sessions
- manual request from the user to “make the plan lighter”

Only one pending proposal is allowed per active plan.

Если новый trigger срабатывает при уже существующем `pending` proposal:

- старый proposal переводится в `expired`
- новый proposal становится единственным active review item

Proposal change types are fixed:

- `shorten_session`
- `reduce_weekly_frequency`
- `insert_recovery_block`
- `insert_wellbeing_block`
- `extend_timeline`

Proposal builder must follow the locked priority order:

1. shorten session duration
2. reduce weekly frequency
3. insert recovery and wellbeing tasks
4. extend the total timeline only if the first three actions do not remove
   overload risk

Acceptance criteria стадии:

- wellbeing never mutates the plan silently
- each proposal has a human-readable rationale
- proposal acceptance produces a traceable history entry

### Stage 5. ICS Parity and Export Ownership

Цель стадии:

- сделать `.ics` export честным отражением active calendar, а не frontend
  approximation

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
- after one release cycle, docs should move user guidance to `GET /calendar/export-ics`

Acceptance criteria стадии:

- exported `.ics` matches the visible active calendar
- export no longer depends on frontend-local saved plan state
- compatibility behavior is explicit and temporary

### Stage 6. Frontend Flows and UX States

Цель стадии:

- провести пользователя через generation, activation, daily use, manual edits
  и proposal review без UX ambiguity

Later frontend flow is fixed as follows:

1. user generates a plan in `plan` view
2. frontend shows draft plan with activation CTA
3. user activates the plan
4. frontend switches to `calendar` view or offers direct navigation there
5. calendar view shows:
   - current active schedule
   - manual edit affordances
   - wellbeing trend graph
   - pending proposal card if present
6. chat view may show a lightweight banner when a new schedule proposal exists
7. user can accept or reject proposal from chat or calendar view

Later localStorage policy:

- localStorage may cache:
  - last selected month or view mode
  - last fetched active calendar snapshot
  - UI-only panel state
- localStorage must not remain canonical for:
  - active plan content
  - event statuses
  - accepted proposals

Later RU-first UI copy updates will be required in:

- `frontend/src/config/ui.ru.ts`
- `frontend/src/config/ui.en.ts`
- `frontend/src/config/ui.types.ts`

Acceptance criteria стадии:

- user всегда понимает, находится ли он в draft plan или active calendar
- proposal review доступен минимум из одного primary flow и одного secondary flow
- local cache не создает conflicting truth with backend

### Stage 7. Regression, Documentation, and Release Criteria

Цель стадии:

- сделать active calendar extension inspectable, regression-safe и легко
  защищаемым на demo

Later routes to implement:

- `GET /career/plan/active`
- `POST /career/plan/activate`
- `GET /calendar/active`
- `PATCH /calendar/events/{event_id}`
- `POST /calendar/proposals/{proposal_id}/accept`
- `POST /calendar/proposals/{proposal_id}/reject`
- `GET /calendar/export-ics`

Later tests must include:

- activation flow
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

- `docs/DECISIONS.ru.md`
- `docs/STATUS.ru.md`
- `docs/ROADMAP.ru.md`
- `docs/STUDENT_MANUAL.ru.md`
- `docs/SETUP.ru.md` if new frontend dependencies or workflows are added

Release criteria for this extension:

1. active plan persists on the backend
2. one active plan per user is enforced
3. FullCalendar view renders persisted events correctly
4. manual edits survive reload and cross-session use
5. wellbeing trend graph renders real backend data
6. proposals are reviewable and never auto-applied
7. `.ics` export matches persisted event state

## Explicitly Out of Scope for This Stage

- autonomous rescheduling without confirmation
- multi-user shared calendars
- Google Calendar or Outlook direct sync
- external notifications or reminder infrastructure
- replacing the existing plan-generation endpoint with a frontend-only planner

## External References

- FullCalendar React docs
  - <https://fullcalendar.io/docs/react>
- Recharts GitHub
  - <https://github.com/recharts/recharts>
- Recharts docs
  - <https://recharts.github.io/>

## Практический итог

Этот план переводит расписание из current preview mode в backend-owned active
calendar system с user-approved adaptive changes.

Он намеренно зависит от wellbeing signal layer, описанного в:

- `codex_plan_wellbeing_rag_and_signals.ru.md`

До реализации этого плана live-система все еще остается на current
schedule-preview + `.ics` export model.
