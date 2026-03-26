import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import App from "./App";
import { getUiText } from "./config/ui";

describe("frontend UI language behavior", () => {
  it("defaults the UI language to Russian and persists it", async () => {
    render(<App />);

    expect(screen.getByRole("button", { name: "Выбрать профиль" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Новый чат" })).toBeInTheDocument();

    await waitFor(() => {
      expect(document.documentElement.lang).toBe("ru");
      expect(document.cookie).toContain("careerguide_ui_language=ru");
    });
  });

  it("restores English from the stored language cookie", async () => {
    document.cookie = "careerguide_ui_language=en; Path=/";
    const englishUi = getUiText("en");

    render(<App />);

    expect(screen.getByRole("button", { name: "Use profile" })).toBeInTheDocument();
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

    expect(screen.getByRole("button", { name: "Выбрать профиль" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "EN" }));

    expect(screen.getByRole("button", { name: "Use profile" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "New chat" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Выбрать профиль" })).not.toBeInTheDocument();

    await waitFor(() => {
      expect(document.cookie).toContain("careerguide_ui_language=en");
      expect(document.documentElement.lang).toBe("en");
    });
  });
});
