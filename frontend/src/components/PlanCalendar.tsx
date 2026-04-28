import { useEffect, useMemo, useState } from "react";

import type { CareerPlanCalendarEvent, CareerPlanResponse } from "../api/client";
import type { UiText } from "../config/ui";

type PlanCalendarProps = {
  plan: CareerPlanResponse;
  uiText: UiText;
  onDeleteEvent: (event: CareerPlanCalendarEvent) => void;
};

function parseEventDate(value: string): Date {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? new Date() : parsed;
}

function dateKey(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function monthKey(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function startOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function addMonths(date: Date, amount: number): Date {
  return new Date(date.getFullYear(), date.getMonth() + amount, 1);
}

function buildMonthDays(activeMonth: Date): Date[] {
  const firstDay = startOfMonth(activeMonth);
  const gridStart = new Date(firstDay);
  gridStart.setDate(firstDay.getDate() - firstDay.getDay());
  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(gridStart);
    date.setDate(gridStart.getDate() + index);
    return date;
  });
}

function eventIdentity(event: CareerPlanCalendarEvent, index: number): string {
  return event.event_id ?? `${event.starts_at}-${event.title}-${index}`;
}

function formatEventTime(event: CareerPlanCalendarEvent, locale: string): string {
  const startsAt = parseEventDate(event.starts_at);
  const endsAt = parseEventDate(event.ends_at);
  const formatter = new Intl.DateTimeFormat(locale, {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${formatter.format(startsAt)} - ${formatter.format(endsAt)}`;
}

function formatEventDate(event: CareerPlanCalendarEvent, locale: string): string {
  return new Intl.DateTimeFormat(locale, {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(parseEventDate(event.starts_at));
}

export function PlanCalendar({ plan, uiText, onDeleteEvent }: PlanCalendarProps) {
  const sortedEvents = useMemo(
    () =>
      [...plan.calendar_events].sort((left, right) =>
        left.starts_at.localeCompare(right.starts_at),
      ),
    [plan.calendar_events],
  );
  const firstEventDate = sortedEvents[0] ? parseEventDate(sortedEvents[0].starts_at) : new Date();
  const [activeMonth, setActiveMonth] = useState(() => startOfMonth(firstEventDate));
  const [selectedEventId, setSelectedEventId] = useState<string | null>(
    sortedEvents[0] ? eventIdentity(sortedEvents[0], 0) : null,
  );

  const eventsWithIds = useMemo(
    () => sortedEvents.map((event, index) => ({ event, id: eventIdentity(event, index) })),
    [sortedEvents],
  );
  const selectedEvent = eventsWithIds.find(({ id }) => id === selectedEventId)?.event ?? null;
  const activeMonthEvents = eventsWithIds.filter(({ event }) => monthKey(parseEventDate(event.starts_at)) === monthKey(activeMonth));
  const eventsByDate = new Map<string, Array<{ event: CareerPlanCalendarEvent; id: string }>>();
  for (const item of activeMonthEvents) {
    const key = dateKey(parseEventDate(item.event.starts_at));
    eventsByDate.set(key, [...(eventsByDate.get(key) ?? []), item]);
  }
  const monthDays = buildMonthDays(activeMonth);
  const monthLabel = new Intl.DateTimeFormat(uiText.metadata.locale, {
    month: "long",
    year: "numeric",
  }).format(activeMonth);

  useEffect(() => {
    if (selectedEvent && plan.calendar_events.includes(selectedEvent)) {
      return;
    }
    setSelectedEventId(eventsWithIds[0]?.id ?? null);
  }, [eventsWithIds, plan.calendar_events, selectedEvent]);

  return (
    <div className="calendar-layout">
      <section className="calendar-month-panel">
        <div className="calendar-toolbar">
          <div>
            <p className="sidebar-eyebrow">{uiText.plan.calendarEyebrow}</p>
            <h3>{monthLabel}</h3>
          </div>
          <div className="toolbar-actions">
            <button className="toolbar-button secondary" type="button" onClick={() => setActiveMonth(addMonths(activeMonth, -1))}>
              {uiText.plan.calendarPrevious}
            </button>
            <button className="toolbar-button secondary" type="button" onClick={() => setActiveMonth(startOfMonth(new Date()))}>
              {uiText.plan.calendarToday}
            </button>
            <button className="toolbar-button secondary" type="button" onClick={() => setActiveMonth(addMonths(activeMonth, 1))}>
              {uiText.plan.calendarNext}
            </button>
          </div>
        </div>

        <div className="calendar-legend">
          <span><span className="legend-dot study" />{uiText.plan.calendarStudy}</span>
          <span><span className="legend-dot break" />{uiText.plan.calendarBreak}</span>
        </div>

        <div className="calendar-grid">
          {monthDays.map((day) => {
            const key = dateKey(day);
            const dayEvents = eventsByDate.get(key) ?? [];
            const isMuted = day.getMonth() !== activeMonth.getMonth();
            const isToday = key === dateKey(new Date());
            return (
              <div key={key} className={`calendar-day ${isMuted ? "muted" : ""} ${isToday ? "today" : ""}`}>
                <span className="calendar-day-number">{day.getDate()}</span>
                <div className="calendar-event-stack">
                  {dayEvents.slice(0, 3).map(({ event, id }) => (
                    <button
                      key={id}
                      className={`calendar-event-chip ${event.event_type === "break" ? "break" : "study"} ${id === selectedEventId ? "active" : ""}`}
                      type="button"
                      onClick={() => setSelectedEventId(id)}
                    >
                      {event.title}
                    </button>
                  ))}
                  {dayEvents.length > 3 ? <span className="calendar-more">+{dayEvents.length - 3}</span> : null}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <aside className="calendar-agenda-panel">
        <p className="sidebar-eyebrow">{uiText.plan.calendarAgenda}</p>
        {activeMonthEvents.length ? (
          <ol className="calendar-agenda-list">
            {activeMonthEvents.map(({ event, id }) => (
              <li key={id}>
                <button
                  className={`calendar-agenda-item ${id === selectedEventId ? "active" : ""}`}
                  type="button"
                  onClick={() => setSelectedEventId(id)}
                >
                  <span>{formatEventDate(event, uiText.metadata.locale)}</span>
                  <strong>{event.title}</strong>
                  <span>{formatEventTime(event, uiText.metadata.locale)}</span>
                </button>
              </li>
            ))}
          </ol>
        ) : (
          <p className="panel-copy">{uiText.plan.calendarNoEvents}</p>
        )}

        <div className="calendar-selected-card">
          <p className="sidebar-eyebrow">{uiText.plan.calendarSelectedEvent}</p>
          {selectedEvent ? (
            <>
              <h4>{selectedEvent.title}</h4>
              <p>{selectedEvent.description}</p>
              <p className="metric">{formatEventDate(selectedEvent, uiText.metadata.locale)} · {formatEventTime(selectedEvent, uiText.metadata.locale)}</p>
              <span className={`pill ${selectedEvent.event_type === "break" ? "break-pill" : ""}`}>
                {selectedEvent.event_type === "break" ? uiText.plan.calendarBreak : uiText.plan.calendarStudy}
              </span>
              <button className="toolbar-button secondary" type="button" onClick={() => onDeleteEvent(selectedEvent)}>
                {uiText.plan.deleteSession}
              </button>
            </>
          ) : (
            <p className="panel-copy">{uiText.plan.calendarNoEventSelected}</p>
          )}
        </div>
      </aside>
    </div>
  );
}
