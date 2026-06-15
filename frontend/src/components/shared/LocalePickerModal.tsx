"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "@/hooks/use-translation";
import { useUserStore } from "@/store/user-store";
import { useSettingsStore } from "@/store/settings-store";
import { userService } from "@/services/api";
import { onLocaleChanged } from "@/lib/locale-sync";
import { useToast } from "@/hooks/use-toast";
import type { AppLocale } from "@/lib/i18n/translations";

export function LocalePickerModal() {
  const user = useUserStore((s) => s.user);
  const setUser = useUserStore((s) => s.setUser);
  const setLanguage = useSettingsStore((s) => s.setLanguage);
  const { t } = useTranslation();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [dismissed, setDismissed] = useState(false);

  const mutation = useMutation({
    mutationFn: (locale: AppLocale) => userService.updateLocale(locale),
    onSuccess: (updated) => {
      setUser(updated);
      setLanguage(updated.language_code);
      onLocaleChanged(queryClient, updated.language_code as AppLocale);
      toast(t("locale.saved"), "success");
      setDismissed(true);
    },
  });

  const visible = user && user.locale_selected === false && !dismissed;
  if (!visible) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-end justify-center bg-black/70 p-4 sm:items-center">
      <div className="glass-strong w-full max-w-sm rounded-3xl p-6 shadow-glow">
        <h2 className="text-lg font-bold">{t("locale.chooseTitle")}</h2>
        <p className="mt-2 text-sm text-text-muted">{t("locale.chooseSubtitle")}</p>
        <div className="mt-6 flex flex-col gap-3">
          <button
            type="button"
            disabled={mutation.isPending}
            onClick={() => mutation.mutate("ru")}
            className="rounded-2xl bg-accent/20 py-3 text-sm font-semibold text-accent-light"
          >
            🇷🇺 {t("profile.languageRu")}
          </button>
          <button
            type="button"
            disabled={mutation.isPending}
            onClick={() => mutation.mutate("en")}
            className="rounded-2xl bg-accent/20 py-3 text-sm font-semibold text-accent-light"
          >
            🇬🇧 {t("profile.languageEn")}
          </button>
        </div>
      </div>
    </div>
  );
}
