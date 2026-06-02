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
    <div className="px-4 pt-6 max-w-lg mx-auto space-y-4">
      <h1 className="text-xl font-bold">Settings</h1>

      <Card className="space-y-4">
        <SettingRow label="Language">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="bg-bg-elevated rounded-sm px-2 py-1 text-sm outline-none"
          >
            <option value="en">English</option>
            <option value="ru">Русский</option>
            <option value="ja">日本語</option>
          </select>
        </SettingRow>

        <SettingRow label="Notifications">
          <Toggle checked={notifications} onChange={setNotifications} />
        </SettingRow>

        <SettingRow label="NSFW Content">
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
      className={`w-10 h-6 rounded-full transition-colors ${checked ? "bg-accent" : "bg-bg-elevated"}`}
    >
      <div
        className={`w-4 h-4 rounded-full bg-white transition-transform mx-1 ${
          checked ? "translate-x-4" : "translate-x-0"
        }`}
      />
    </button>
  );
}
