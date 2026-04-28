import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import App from "./App";
import type { CareerPlanResponse } from "./api/client";
import { getUiText } from "./config/ui";

function makeSavedPlan(overrides: Partial<CareerPlanResponse> = {}): CareerPlanResponse {
  return {
    goal: "Build a transition plan into data analytics",
    target_role: "Data Analyst",
    workload_level: "medium",
    estimated_weeks: 1,
    study_preferences: {
      study_start_date: "2026-04-06",
      preferred_study_time: "evening",
      study_frequency_per_week: 3,
      session_duration_minutes: 90,
      timezone: "UTC",
    },
    steps: [
      {
        title: "Learn SQL",
        description: "Practice querying a small dataset.",
        focus_skills: ["SQL"],
      },
    ],
    calendar_events: [
      {
        event_id: "evt-test-study",
        event_type: "study",
        title: "Data Analyst: Learn SQL",
        description: "Focus topics: SQL.",
        starts_at: "2026-04-06T19:00:00",
        ends_at: "2026-04-06T20:30:00",
        week_index: 1,
        step_index: 1,
        session_index: 1,
        total_sessions: 1,
      },
    ],
    citations: [],
    ...overrides,
  };
}

describe("frontend UI language behavior", () => {
  it("defaults the UI language to Russian and persists it", async () => {
    render(<App />);

    expect(screen.getByRole("button", { name: "Сохранить имя" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "История" })).toBeInTheDocument();

    await waitFor(() => {
      expect(document.documentElement.lang).toBe("ru");
      expect(document.cookie).toContain("careerguide_ui_language=ru");
      const storedProfile = JSON.parse(window.localStorage.getItem("careerguide:local-profile:v1") ?? "{}");
      expect(storedProfile.id).toMatch(/^cg-/);
    });
  });

  it("restores English from the stored language cookie", async () => {
    document.cookie = "careerguide_ui_language=en; Path=/";
    const englishUi = getUiText("en");

    render(<App />);

    expect(screen.getByRole("button", { name: "Save name" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "History" })).toBeInTheDocument();

    await waitFor(() => {
      expect(document.documentElement.lang).toBe("en");
      expect(document.title).toBe(englishUi.metadata.title);
      expect(document.querySelector('meta[name="description"]')?.getAttribute("content")).toBe(
        englishUi.metadata.description,
      );
    });
  });

  it("toggles from Russian to English and updates the persisted cookie", async () => {
    const user = userEvent.setup();

    render(<App />);

    expect(screen.getByRole("button", { name: "Сохранить имя" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "EN" }));

    expect(screen.getByRole("button", { name: "Save name" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "History" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Сохранить имя" })).not.toBeInTheDocument();

    await waitFor(() => {
      expect(document.cookie).toContain("careerguide_ui_language=en");
      expect(document.documentElement.lang).toBe("en");
    });
  });

  it("uses a generated local profile id for backend memory requests", async () => {
    const fetchMock = vi.mocked(fetch);

    render(<App />);

    await waitFor(() => {
      const storedProfile = JSON.parse(window.localStorage.getItem("careerguide:local-profile:v1") ?? "{}");
      expect(storedProfile.id).toMatch(/^cg-/);
      expect(
        fetchMock.mock.calls.some(([input]) =>
          String(input).includes(`/memory/list?user_id=${encodeURIComponent(storedProfile.id)}`),
        ),
      ).toBe(true);
    });
  });

  it("copies and imports profile codes", async () => {
    document.cookie = "careerguide_ui_language=en; Path=/";
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    render(<App />);

    const storedProfile = JSON.parse(window.localStorage.getItem("careerguide:local-profile:v1") ?? "{}");
    await user.click(screen.getByRole("button", { name: "Copy code" }));
    expect(writeText).toHaveBeenCalledWith(storedProfile.id);

    await user.type(screen.getByLabelText("Import profile code"), "cg-shared-profile");
    await user.click(screen.getByRole("button", { name: "Import" }));

    await waitFor(() => {
      const importedProfile = JSON.parse(window.localStorage.getItem("careerguide:local-profile:v1") ?? "{}");
      expect(importedProfile.id).toBe("cg-shared-profile");
    });
  });

  it("stores theme selections per local profile", async () => {
    document.cookie = "careerguide_ui_language=en; Path=/";
    const user = userEvent.setup();

    const { container } = render(<App />);
    const storedProfile = JSON.parse(window.localStorage.getItem("careerguide:local-profile:v1") ?? "{}");

    await user.click(screen.getByRole("button", { name: "Paper" }));

    expect(container.querySelector(".shell-root")).toHaveAttribute("data-theme", "paper");
    expect(window.localStorage.getItem(`careerguide:theme:${storedProfile.id}`)).toBe("paper");
  });

  it("migrates old theme ids to slate and groups sidebar settings", async () => {
    document.cookie = "careerguide_ui_language=en; Path=/";
    window.localStorage.setItem(
      "careerguide:local-profile:v1",
      JSON.stringify({ id: "cg-theme-user", label: "Theme user" }),
    );
    window.localStorage.setItem("careerguide:theme:cg-theme-user", "harbor");

    const { container } = render(<App />);

    expect(container.querySelector(".shell-root")).toHaveAttribute("data-theme", "slate");
    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(screen.getByText("Appearance")).toBeInTheDocument();
    expect(screen.getByText("Language")).toBeInTheDocument();

    await waitFor(() => {
      expect(window.localStorage.getItem("careerguide:theme:cg-theme-user")).toBe("slate");
    });
  });

  it("moves chat history controls into the history workspace", async () => {
    document.cookie = "careerguide_ui_language=en; Path=/";
    const user = userEvent.setup();

    render(<App />);

    expect(screen.queryByRole("button", { name: "New chat" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "History" }));

    expect(screen.getAllByRole("heading", { name: "Chat history" }).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "New chat" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete all" })).toBeInTheDocument();
  });

  it("migrates legacy demo-user conversations and plans to the generated local profile once", async () => {
    const legacyConversations = JSON.stringify([
      {
        id: "legacy-chat",
        title: "Legacy chat",
        createdAt: "2026-04-01T00:00:00.000Z",
        updatedAt: "2026-04-01T00:00:00.000Z",
        messages: [{ id: "assistant-welcome", role: "assistant", text: "Legacy" }],
      },
    ]);
    const legacyPlan = JSON.stringify({
      goal: "Legacy goal",
      targetRole: "Data Analyst",
      savedAt: "2026-04-01T00:00:00.000Z",
      plan: {
        goal: "Legacy goal",
        target_role: "Data Analyst",
        workload_level: "medium",
        estimated_weeks: 1,
        study_preferences: {
          study_start_date: "2026-04-06",
          preferred_study_time: "evening",
          study_frequency_per_week: 3,
          session_duration_minutes: 90,
          timezone: "UTC",
        },
        steps: [],
        calendar_events: [],
        citations: [],
      },
    });
    window.localStorage.setItem("careerguide:conversations:demo-user", legacyConversations);
    window.localStorage.setItem("careerguide:plan:demo-user", legacyPlan);

    render(<App />);

    await waitFor(() => {
      const storedProfile = JSON.parse(window.localStorage.getItem("careerguide:local-profile:v1") ?? "{}");
      const migratedConversations = JSON.parse(
        window.localStorage.getItem(`careerguide:conversations:${storedProfile.id}`) ?? "[]",
      );
      expect(migratedConversations[0]?.id).toBe("legacy-chat");
      expect(window.localStorage.getItem(`careerguide:plan:${storedProfile.id}`)).toBe(legacyPlan);
      expect(window.localStorage.getItem("careerguide:local-profile:migrated-demo-user:v1")).toBe("true");
    });
  });

  it("submits the chat form when Enter is pressed in the composer", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);

    fetchMock.mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input instanceof Request ? input.url : String(input);

      if (url.includes("/chat/answer")) {
        return new Response(
          JSON.stringify({
            answer: "Test answer",
            citations: [],
            prompt_preview: "",
            memory_summary: "",
            response_kind: "answer",
          }),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json",
            },
          },
        );
      }

      return new Response(JSON.stringify([]), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
        },
      });
    });

    render(<App />);

    const composer = screen.getByPlaceholderText(
      "Опишите, что вам подходит, чего вы хотите избежать и какое решение вы сейчас пытаетесь принять.",
    );

    await user.type(composer, "Тестовый вопрос{enter}");

    await waitFor(() => {
      expect(screen.getAllByText("Тестовый вопрос").length).toBeGreaterThanOrEqual(1);
      expect(fetchMock.mock.calls.some(([input]) => String(input).includes("/chat/answer"))).toBe(true);
    });
  });

  it("sends bounded chat context and stores offered plan handoffs per conversation", async () => {
    document.cookie = "careerguide_ui_language=en; Path=/";
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);

    fetchMock.mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input instanceof Request ? input.url : String(input);
      if (url.includes("/chat/answer")) {
        return new Response(
          JSON.stringify({
            answer: "Data Analyst is a clear supported target. Would you like me to move this into a study plan for Data Analyst?",
            citations: [],
            prompt_preview: "",
            memory_summary: "",
            response_kind: "answer",
            plan_handoff: {
              status: "offered",
              target_role: "Data Analyst",
              goal: "Build a realistic transition study plan for Data Analyst",
              source: "supported_role_match",
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });

    render(<App />);

    await user.type(
      screen.getByPlaceholderText("Describe what fits you, what you want to avoid, or what decision you are trying to make."),
      "I want to move into data analytics.{enter}",
    );

    await waitFor(() => {
      expect(screen.getByText(/Data Analyst is a clear supported target/)).toBeInTheDocument();
    });

    const answerCall = fetchMock.mock.calls.find(([input]) => String(input).includes("/chat/answer"));
    const requestBody = JSON.parse(String((answerCall?.[1] as RequestInit).body));
    expect(requestBody.pending_plan_handoff).toBeNull();
    expect(requestBody.conversation_context[requestBody.conversation_context.length - 1]).toMatchObject({
      role: "user",
      text: "I want to move into data analytics.",
    });

    const storedProfile = JSON.parse(window.localStorage.getItem("careerguide:local-profile:v1") ?? "{}");
    const storedConversations = JSON.parse(
      window.localStorage.getItem(`careerguide:conversations:${storedProfile.id}`) ?? "[]",
    );
    expect(storedConversations[0].pendingPlanHandoff.status).toBe("offered");
    expect(storedConversations[0].pendingPlanHandoff.target_role).toBe("Data Analyst");
  });

  it("opens the plan builder on an accepted handoff without overwriting a saved plan", async () => {
    document.cookie = "careerguide_ui_language=en; Path=/";
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);
    const savedBundle = {
      goal: "Existing saved goal",
      targetRole: "Data Analyst",
      savedAt: "2026-04-01T00:00:00.000Z",
      plan: makeSavedPlan({ goal: "Existing saved goal" }),
    };
    window.localStorage.setItem(
      "careerguide:local-profile:v1",
      JSON.stringify({ id: "cg-handoff-user", label: "Handoff user" }),
    );
    window.localStorage.setItem("careerguide:plan:cg-handoff-user", JSON.stringify(savedBundle));

    fetchMock.mockImplementation(async (input, init) => {
      const url = typeof input === "string" ? input : input instanceof Request ? input.url : String(input);
      if (url.includes("/chat/answer")) {
        const body = JSON.parse(String((init as RequestInit).body));
        if (body.pending_plan_handoff) {
          return new Response(
            JSON.stringify({
              answer: "Okay. I’ll open the plan builder with Data Analyst filled in.",
              citations: [],
              prompt_preview: "",
              memory_summary: "",
              response_kind: "answer",
              plan_handoff: {
                status: "accepted",
                target_role: "Data Analyst",
                goal: "Build a realistic transition study plan for Data Analyst",
                source: "supported_role_match",
              },
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response(
          JSON.stringify({
            answer: "Data Analyst is a clear target. Would you like me to move this into a study plan for Data Analyst?",
            citations: [],
            prompt_preview: "",
            memory_summary: "",
            response_kind: "answer",
            plan_handoff: {
              status: "offered",
              target_role: "Data Analyst",
              goal: "Build a realistic transition study plan for Data Analyst",
              source: "supported_role_match",
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });

    render(<App />);

    await user.type(
      screen.getByPlaceholderText("Describe what fits you, what you want to avoid, or what decision you are trying to make."),
      "I want to move into data analytics.{enter}",
    );
    await waitFor(() => {
      expect(screen.getByText(/Data Analyst is a clear target/)).toBeInTheDocument();
    });

    await user.type(
      screen.getByPlaceholderText("Describe what fits you, what you want to avoid, or what decision you are trying to make."),
      "yes{enter}",
    );

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Builder" })).toHaveAttribute("aria-selected", "true");
    });
    expect(screen.getByDisplayValue("Build a realistic transition study plan for Data Analyst")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Data Analyst")).toBeInTheDocument();

    const storedPlan = JSON.parse(window.localStorage.getItem("careerguide:plan:cg-handoff-user") ?? "{}");
    expect(storedPlan.savedAt).toBe(savedBundle.savedAt);
    expect(storedPlan.plan.goal).toBe("Existing saved goal");
  });

  it("clears the pending plan handoff when the user declines", async () => {
    document.cookie = "careerguide_ui_language=en; Path=/";
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);

    fetchMock.mockImplementation(async (input, init) => {
      const url = typeof input === "string" ? input : input instanceof Request ? input.url : String(input);
      if (url.includes("/chat/answer")) {
        const body = JSON.parse(String((init as RequestInit).body));
        if (body.pending_plan_handoff) {
          return new Response(
            JSON.stringify({
              answer: "Okay, we can keep narrowing this in chat without moving to a plan yet.",
              citations: [],
              prompt_preview: "",
              memory_summary: "",
              response_kind: "answer",
              plan_handoff: {
                status: "declined",
                target_role: "Data Analyst",
                goal: "Build a realistic transition study plan for Data Analyst",
                source: "supported_role_match",
              },
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response(
          JSON.stringify({
            answer: "Data Analyst is a clear target. Would you like me to move this into a study plan for Data Analyst?",
            citations: [],
            prompt_preview: "",
            memory_summary: "",
            response_kind: "answer",
            plan_handoff: {
              status: "offered",
              target_role: "Data Analyst",
              goal: "Build a realistic transition study plan for Data Analyst",
              source: "supported_role_match",
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });

    render(<App />);

    await user.type(
      screen.getByPlaceholderText("Describe what fits you, what you want to avoid, or what decision you are trying to make."),
      "I want to move into data analytics.{enter}",
    );
    await waitFor(() => {
      expect(screen.getByText(/Data Analyst is a clear target/)).toBeInTheDocument();
    });

    await user.type(
      screen.getByPlaceholderText("Describe what fits you, what you want to avoid, or what decision you are trying to make."),
      "no{enter}",
    );
    await waitFor(() => {
      expect(screen.getByText(/keep narrowing this in chat/)).toBeInTheDocument();
    });

    const storedProfile = JSON.parse(window.localStorage.getItem("careerguide:local-profile:v1") ?? "{}");
    const storedConversations = JSON.parse(
      window.localStorage.getItem(`careerguide:conversations:${storedProfile.id}`) ?? "[]",
    );
    expect(storedConversations[0].pendingPlanHandoff).toBeNull();
    expect(screen.queryByRole("tab", { name: "Builder" })).not.toBeInTheDocument();
  });

  it("renders limited unsupported chat responses as scope notes", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);

    fetchMock.mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input instanceof Request ? input.url : String(input);

      if (url.includes("/chat/answer")) {
        return new Response(
          JSON.stringify({
            answer: "Ограниченный ответ",
            citations: [],
            prompt_preview: "",
            memory_summary: "",
            response_kind: "limited_unsupported",
          }),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json",
            },
          },
        );
      }

      return new Response(JSON.stringify([]), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
        },
      });
    });

    render(<App />);

    await user.type(
      screen.getByPlaceholderText(
        "Опишите, что вам подходит, чего вы хотите избежать и какое решение вы сейчас пытаетесь принять.",
      ),
      "Неподдерживаемая роль{enter}",
    );

    await waitFor(() => {
      expect(screen.getByText("Ограниченный ответ")).toBeInTheDocument();
    });

    const responseArticle = screen.getByText("Ограниченный ответ").closest("article");
    expect(responseArticle).not.toBeNull();
    expect(within(responseArticle as HTMLElement).getByText("Пояснение по границам")).toBeInTheDocument();
    expect(within(responseArticle as HTMLElement).queryByText("InspiON")).not.toBeInTheDocument();
  });

  it("renders a saved plan calendar and deletes sessions with confirmation", async () => {
    document.cookie = "careerguide_ui_language=en; Path=/";
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    window.localStorage.setItem(
      "careerguide:local-profile:v1",
      JSON.stringify({ id: "cg-calendar-user", label: "Calendar user" }),
    );
    window.localStorage.setItem(
      "careerguide:plan:cg-calendar-user",
      JSON.stringify({
        goal: "Build a transition plan into data analytics",
        targetRole: "Data Analyst",
        savedAt: "2026-04-01T00:00:00.000Z",
        plan: makeSavedPlan(),
      }),
    );

    render(<App />);

    await user.click(screen.getByRole("button", { name: "Plan" }));
    expect(screen.getByRole("tab", { name: "Calendar" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getAllByText("Data Analyst: Learn SQL").length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: "Delete session" }));

    await waitFor(() => {
      const storedPlan = JSON.parse(window.localStorage.getItem("careerguide:plan:cg-calendar-user") ?? "{}");
      expect(storedPlan.plan.calendar_events).toHaveLength(0);
    });
  });

  it("applies chat-suggested plan updates to the saved local plan", async () => {
    document.cookie = "careerguide_ui_language=en; Path=/";
    const user = userEvent.setup();
    const fetchMock = vi.mocked(fetch);
    const updatedPlan = makeSavedPlan({
      study_preferences: {
        study_start_date: "2026-04-06",
        preferred_study_time: "evening",
        study_frequency_per_week: 2,
        session_duration_minutes: 60,
        timezone: "UTC",
      },
      workload_level: "low",
    });
    window.localStorage.setItem(
      "careerguide:local-profile:v1",
      JSON.stringify({ id: "cg-plan-update-user", label: "Plan user" }),
    );
    window.localStorage.setItem(
      "careerguide:plan:cg-plan-update-user",
      JSON.stringify({
        goal: "Build a transition plan into data analytics",
        targetRole: "Data Analyst",
        savedAt: "2026-04-01T00:00:00.000Z",
        plan: makeSavedPlan(),
      }),
    );

    fetchMock.mockImplementation(async (input) => {
      const url = typeof input === "string" ? input : input instanceof Request ? input.url : String(input);
      if (url.includes("/chat/answer")) {
        return new Response(
          JSON.stringify({
            answer: "I suggest lowering the study load.",
            citations: [],
            prompt_preview: "",
            memory_summary: "",
            response_kind: "answer",
            plan_update: {
              kind: "relax_schedule",
              summary: "I suggest lowering the study load.",
              updated_plan: updatedPlan,
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });

    render(<App />);

    await user.click(screen.getByRole("button", { name: "Chat" }));
    await user.type(
      screen.getByPlaceholderText("Describe what fits you, what you want to avoid, or what decision you are trying to make."),
      "Please relax my study plan.{enter}",
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Apply updated plan" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Apply updated plan" }));

    const storedPlan = JSON.parse(window.localStorage.getItem("careerguide:plan:cg-plan-update-user") ?? "{}");
    expect(storedPlan.plan.workload_level).toBe("low");
    expect(storedPlan.plan.study_preferences.study_frequency_per_week).toBe(2);
  });
});
