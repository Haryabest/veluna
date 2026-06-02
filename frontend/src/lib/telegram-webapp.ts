"use client";

export function getTelegramWebApp(): TelegramWebAppLite | null {
  if (typeof window === "undefined") return null;
  return (window as unknown as { Telegram?: { WebApp?: TelegramWebAppLite } }).Telegram
    ?.WebApp ?? null;
}

/** Mini App opened inside Telegram (has initData). */
export function isTelegramWebApp(): boolean {
  const tg = getTelegramWebApp();
  return Boolean(tg?.initData && tg.initData.length > 0);
}

/** Stars invoice can only be opened from Telegram client. */
export function canPayWithTelegramStars(): boolean {
  const tg = getTelegramWebApp();
  return typeof tg?.openInvoice === "function";
}

interface TelegramWebAppLite {
  initData: string;
  openInvoice?: (url: string, callback?: (status: string) => void) => void;
  ready?: () => void;
  expand?: () => void;
}
