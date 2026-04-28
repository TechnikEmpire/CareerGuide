import { uiTextEn } from "./ui.en";
import { uiTextRu } from "./ui.ru";
import type { UiLanguage, UiText } from "./ui.types";

const UI_LANGUAGE_COOKIE = "careerguide_ui_language";
const COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365;

export type { ThemeId, UiLanguage, UiText } from "./ui.types";

export function normalizeUiLanguage(value: string | null | undefined): UiLanguage {
  return value === "en" ? "en" : "ru";
}

export function getUiText(language: UiLanguage): UiText {
  return language === "en" ? uiTextEn : uiTextRu;
}

export function readStoredUiLanguage(): UiLanguage {
  if (typeof document === "undefined") {
    return "ru";
  }

  const cookie = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(`${UI_LANGUAGE_COOKIE}=`));
  if (!cookie) {
    return "ru";
  }

  const value = cookie.slice(`${UI_LANGUAGE_COOKIE}=`.length);
  return normalizeUiLanguage(decodeURIComponent(value));
}

export function persistUiLanguage(language: UiLanguage): void {
  if (typeof document === "undefined") {
    return;
  }

  document.cookie =
    `${UI_LANGUAGE_COOKIE}=${encodeURIComponent(language)}; ` +
    `Max-Age=${COOKIE_MAX_AGE_SECONDS}; Path=/; SameSite=Lax`;
}
