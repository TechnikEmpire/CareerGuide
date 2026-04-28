import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import App from "./App";
import { getUiText } from "./config/ui";

describe("frontend UI language behavior", () => {
  it("defaults the UI language to Russian and persists it", async () => {
    render(<App />);

    expect(screen.getByRole("button", { name: "Сохранить имя" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Новый чат" })).toBeInTheDocument();

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
    expect(screen.getByRole("button", { name: "New chat" })).toBeInTheDocument();

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
    expect(screen.getByRole("button", { name: "New chat" })).toBeInTheDocument();
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

    await user.click(screen.getByRole("button", { name: "Harbor" }));

    expect(container.querySelector(".shell-root")).toHaveAttribute("data-theme", "harbor");
    expect(window.localStorage.getItem(`careerguide:theme:${storedProfile.id}`)).toBe("harbor");
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
      expect(screen.getAllByText("Тестовый вопрос").length).toBeGreaterThanOrEqual(2);
      expect(fetchMock.mock.calls.some(([input]) => String(input).includes("/chat/answer"))).toBe(true);
    });
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
});
