import {
  t,
  normalizeLocale,
  type AppLocale,
  type TranslationKey,
} from "@/lib/i18n/translations";
import { useSettingsStore } from "@/store/settings-store";

function currentLocale(): AppLocale {
  if (typeof window === "undefined") return "ru";
  return normalizeLocale(useSettingsStore.getState().language);
}

export function translateGenerationStatus(status: string, locale?: AppLocale): string {
  const loc = locale ?? currentLocale();
  const key = `gen.status.${status}` as TranslationKey;
  const mapped = t(loc, key);
  return mapped !== key ? mapped : status;
}

const API_ERROR_KEYS: Record<string, TranslationKey> = {
  "Unknown error": "error.unknown",
  "Network Error": "error.network",
  "Request failed with status code 401": "error.sessionExpired",
  "Request failed with status code 403": "error.forbidden",
  "Request failed with status code 404": "error.notFound",
  "Request failed with status code 429": "error.tooManyRequests",
};

export function translateApiError(message: string, locale?: AppLocale): string {
  const loc = locale ?? currentLocale();
  const key = API_ERROR_KEYS[message];
  if (key) return t(loc, key);
  return message;
}
