"use client";

import { useCallback } from "react";
import {
  t as translate,
  type AppLocale,
  type TranslationKey,
  normalizeLocale,
} from "@/lib/i18n/translations";
import { useSettingsStore } from "@/store/settings-store";

export function useTranslation() {
  const language = useSettingsStore((s) => s.language);
  const locale = normalizeLocale(language);

  const t = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>) =>
      translate(locale, key, params),
    [locale]
  );

  return { t, locale };
}

export function useAppLocale(): AppLocale {
  return normalizeLocale(useSettingsStore((s) => s.language));
}
