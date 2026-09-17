import type { Locale } from "./i18n";
import pt from "@/messages/pt.json";
import en from "@/messages/en.json";
import es from "@/messages/es.json";

const dictionaries: Record<Locale, typeof pt> = { pt, en, es };

export function getDictionary(locale: Locale) {
  return dictionaries[locale];
}
