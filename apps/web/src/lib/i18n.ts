// Mirrors src/tikdrop/i18n.py on the backend - add a language there AND here when adding one.
export const SUPPORTED_LOCALES = ["pt", "en", "es"] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "pt";

export const LOCALE_NAMES: Record<Locale, string> = {
  pt: "Português",
  en: "English",
  es: "Español",
};

export function isValidLocale(value: string): value is Locale {
  return (SUPPORTED_LOCALES as readonly string[]).includes(value);
}
