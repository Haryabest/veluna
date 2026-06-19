"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useSettingsStore } from "@/store/settings-store";
import { useUserStore } from "@/store/user-store";
import { ListPanel } from "@/components/shared/ListPanel";
import { chatSeparatorStyle } from "@/lib/theme";
import { useTranslation } from "@/hooks/use-translation";
import { useToast } from "@/hooks/use-toast";
import { userService } from "@/services/api";
import { onLocaleChanged } from "@/lib/locale-sync";
import type { AppLocale } from "@/lib/i18n/translations";

export default function SettingsPage() {
  const {
    language,
    notifications,
    nsfwEnabled,
    setLanguage,
    setNotifications,
    setNsfwEnabled,
  } = useSettingsStore();
  const setUser = useUserStore((s) => s.setUser);
  const { t } = useTranslation();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const localeMutation = useMutation({
    mutationFn: (next: AppLocale) => userService.updateLocale(next),
    onSuccess: (updated) => {
      setUser(updated);
      setLanguage(updated.language_code);
      onLocaleChanged(queryClient, updated.language_code as AppLocale);
      toast(t("locale.saved"), "success");
    },
  });

  return (
    <div className="mx-auto max-w-lg space-y-4 px-4 pb-28 pt-6">
      <h1 className="text-xl font-bold">{t("settings.title")}</h1>

      <ListPanel>
        <SettingRow label={t("settings.language")} showSeparator>
          <select
            value={language}
            disabled={localeMutation.isPending}
            onChange={(e) => {
              const next = e.target.value as AppLocale;
              setLanguage(next);
              localeMutation.mutate(next);
            }}
            className="rounded-lg bg-bg-elevated px-2 py-1 text-sm outline-none"
          >
            <option value="ru">{t("profile.languageRu")}</option>
            <option value="en">{t("profile.languageEn")}</option>
          </select>
        </SettingRow>

        <SettingRow label={t("settings.notifications")} showSeparator>
          <Toggle
            checked={notifications}
            onChange={setNotifications}
            ariaOn={t("settings.toggleOn")}
            ariaOff={t("settings.toggleOff")}
          />
        </SettingRow>

        <SettingRow label={t("settings.nsfw")}>
          <Toggle
            checked={nsfwEnabled}
            onChange={setNsfwEnabled}
            ariaOn={t("settings.toggleOn")}
            ariaOff={t("settings.toggleOff")}
          />
        </SettingRow>
      </ListPanel>
    </div>
  );
}

function SettingRow({
  label,
  children,
  showSeparator,
}: {
  label: string;
  children: React.ReactNode;
  showSeparator?: boolean;
}) {
  return (
    <div
      className="flex items-center justify-between px-4 py-3.5"
      style={showSeparator ? chatSeparatorStyle : undefined}
    >
      <span className="text-sm text-text-secondary">{label}</span>
      {children}
    </div>
  );
}

function Toggle({
  checked,
  onChange,
  ariaOn,
  ariaOff,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  ariaOn: string;
  ariaOff: string;
}) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={`h-6 w-10 rounded-full transition-colors ${checked ? "bg-accent" : "bg-bg-elevated"}`}
      aria-label={checked ? ariaOff : ariaOn}
    >
      <div
        className={`mx-1 h-4 w-4 rounded-full bg-text-primary transition-transform ${
          checked ? "translate-x-4" : "translate-x-0"
        }`}
      />
    </button>
  );
}
