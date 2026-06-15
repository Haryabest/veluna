"use client";

import { useEffect } from "react";
import { useUserStore } from "@/store/user-store";
import { useSettingsStore } from "@/store/settings-store";
import { normalizeLocale } from "@/lib/i18n/translations";

/** Sync Zustand language from API user profile. */
export function LocaleSync() {
  const user = useUserStore((s) => s.user);
  const setLanguage = useSettingsStore((s) => s.setLanguage);

  useEffect(() => {
    if (user?.language_code) {
      setLanguage(normalizeLocale(user.language_code));
    }
  }, [user?.language_code, setLanguage]);

  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.lang = normalizeLocale(user?.language_code ?? useSettingsStore.getState().language);
    }
  }, [user?.language_code]);

  return null;
}
