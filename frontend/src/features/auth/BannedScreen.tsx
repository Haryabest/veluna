"use client";

import { useTranslation } from "@/hooks/use-translation";

export interface BanInfo {
  message: string;
  ban_reason?: string | null;
  banned_until?: string | null;
}

function formatBannedUntil(iso: string | null | undefined, locale: "ru" | "en"): string | null {
  if (!iso) return null;
  try {
    const dt = new Date(iso);
    return dt.toLocaleString(locale === "en" ? "en-US" : "ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Europe/Moscow",
    });
  } catch {
    return null;
  }
}

export function BannedScreen({ ban }: { ban: BanInfo }) {
  const { t, locale } = useTranslation();
  const until = formatBannedUntil(ban.banned_until, locale);
  const reason = ban.ban_reason?.trim();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-5 p-6 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-500/15 text-3xl">
        🚫
      </div>
      <div className="max-w-sm space-y-3">
        <h1 className="text-lg font-semibold text-text-primary">{t("banned.title")}</h1>
        <p className="text-sm leading-relaxed text-text-muted whitespace-pre-line">{ban.message}</p>
        {reason ? (
          <p className="rounded-xl bg-bg-elevated/80 px-4 py-3 text-sm text-text-primary">
            <span className="text-text-muted">{t("banned.reason")} </span>
            {reason}
          </p>
        ) : null}
        {until ? (
          <p className="text-xs text-text-muted">{t("banned.until").replace("{date}", until)}</p>
        ) : (
          <p className="text-xs text-text-muted">{t("banned.forever")}</p>
        )}
      </div>
    </div>
  );
}
