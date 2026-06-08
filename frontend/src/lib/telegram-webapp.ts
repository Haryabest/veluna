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

/** Signed launch data from Telegram — used to re-auth when JWT expired. */
export function getTelegramInitData(): string | null {
  const raw = getTelegramWebApp()?.initData?.trim();
  return raw || null;
}

/** Stars invoice can only be opened from Telegram client. */
export function canPayWithTelegramStars(): boolean {
  const tg = getTelegramWebApp();
  return typeof tg?.openInvoice === "function";
}

export interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
  is_premium?: boolean;
}

interface TelegramWebAppLite {
  initData: string;
  initDataUnsafe?: { user?: TelegramUser };
  openInvoice?: (url: string, callback?: (status: string) => void) => void;
  openTelegramLink?: (url: string) => void;
  shareMessage?: (msgId: string, callback?: (success: boolean) => void) => void;
  ready?: () => void;
  expand?: () => void;
}

/** Данные профиля из Telegram Mini App */
export function getTelegramUser(): TelegramUser | null {
  return getTelegramWebApp()?.initDataUnsafe?.user ?? null;
}

export function getTelegramDisplayName(user: TelegramUser | null): string {
  if (!user) return "Гость";
  return [user.first_name, user.last_name].filter(Boolean).join(" ");
}
