"use client";

import { useSettingsStore } from "@/store/settings-store";
import { Card } from "@/components/shared/Card";

export default function SettingsPage() {
  const {
    language,
    notifications,
    nsfwEnabled,
    setLanguage,
    setNotifications,
    setNsfwEnabled,
  } = useSettingsStore();

  return (
    <div className="mx-auto max-w-lg space-y-4 px-4 pb-28 pt-6">
      <h1 className="text-xl font-bold">Настройки</h1>

      <Card className="space-y-4">
        <SettingRow label="Язык">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="rounded-lg bg-bg-elevated px-2 py-1 text-sm outline-none"
          >
            <option value="ru">Русский</option>
            <option value="en">English</option>
            <option value="ja">日本語</option>
          </select>
        </SettingRow>

        <SettingRow label="Уведомления">
          <Toggle checked={notifications} onChange={setNotifications} />
        </SettingRow>

        <SettingRow label="NSFW-контент">
          <Toggle checked={nsfwEnabled} onChange={setNsfwEnabled} />
        </SettingRow>
      </Card>
    </div>
  );
}

function SettingRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-text-secondary">{label}</span>
      {children}
    </div>
  );
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={`h-6 w-10 rounded-full transition-colors ${checked ? "bg-accent" : "bg-bg-elevated"}`}
      aria-label={checked ? "Выключить" : "Включить"}
    >
      <div
        className={`mx-1 h-4 w-4 rounded-full bg-white transition-transform ${
          checked ? "translate-x-4" : "translate-x-0"
        }`}
      />
    </button>
  );
}
