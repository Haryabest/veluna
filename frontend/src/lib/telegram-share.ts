"use client";

import { getTelegramWebApp, isTelegramWebApp } from "@/lib/telegram-webapp";

const BOT_LINK = (process.env.NEXT_PUBLIC_TELEGRAM_BOT_LINK || "").trim();

interface TelegramWebAppShare {
  shareMessage?: (
    msgId: string,
    callback?: (success: boolean) => void
  ) => void;
  openTelegramLink?: (url: string) => void;
  openLink?: (url: string) => void;
}

export function getTelegramBotLink(fallback?: string): string {
  return BOT_LINK || fallback?.trim() || "";
}

function openExternalUrl(url: string) {
  const tg = getTelegramWebApp() as TelegramWebAppShare | null;
  if (tg?.openTelegramLink) {
    tg.openTelegramLink(url);
    return;
  }
  if (tg?.openLink) {
    tg.openLink(url);
    return;
  }
  if (typeof window !== "undefined") {
    window.open(url, "_blank", "noopener,noreferrer");
  }
}

/** Opens native Telegram share with image URL. */
export function openTelegramImageShare(imageUrl: string, botLink?: string) {
  const link = botLink || getTelegramBotLink();
  const text = link ? `Смотри какой арт!\n\n${link}` : "Смотри какой арт!";
  const shareUrl = `https://t.me/share/url?${new URLSearchParams({
    url: imageUrl,
    text,
  }).toString()}`;
  openExternalUrl(shareUrl);
}

/** Opens native Telegram chat picker to share text + bot link (fallback). */
export function openTelegramTextShare(botLink: string, imageUrl?: string) {
  const link = botLink || getTelegramBotLink();
  const parts = ["Смотри какой арт!"];
  if (imageUrl) parts.push(imageUrl);
  if (link) parts.push(link);
  const text = parts.join("\n\n");
  const shareUrl = `https://t.me/share/url?${new URLSearchParams({
    ...(link ? { url: link } : imageUrl ? { url: imageUrl } : {}),
    text,
  }).toString()}`;
  openExternalUrl(shareUrl);
}

/** Share prepared photo message via Telegram Mini App (opens chat picker). */
export function sharePreparedTelegramMessage(preparedMessageId: string): Promise<boolean> {
  return new Promise((resolve) => {
    const tg = getTelegramWebApp() as TelegramWebAppShare | null;
    if (!tg?.shareMessage) {
      resolve(false);
      return;
    }
    try {
      tg.shareMessage(preparedMessageId, (success) => resolve(Boolean(success)));
    } catch {
      resolve(false);
    }
  });
}

export function canShareViaTelegram(): boolean {
  return isTelegramWebApp();
}
