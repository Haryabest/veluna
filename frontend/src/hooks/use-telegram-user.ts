"use client";

import { useEffect, useState } from "react";
import {
  getTelegramDisplayName,
  getTelegramUser,
  getTelegramWebApp,
  type TelegramUser,
} from "@/lib/telegram-webapp";

export function useTelegramUser() {
  const [tgUser, setTgUser] = useState<TelegramUser | null>(null);

  useEffect(() => {
    const refresh = () => setTgUser(getTelegramUser());
    const tg = getTelegramWebApp();
    tg?.ready?.();
    refresh();

    // initDataUnsafe.user (incl. photo_url) may appear shortly after WebApp init
    const timers = [100, 400, 1200].map((ms) => window.setTimeout(refresh, ms));
    return () => timers.forEach(clearTimeout);
  }, []);

  return {
    tgUser,
    displayName: getTelegramDisplayName(tgUser),
    username: tgUser?.username ?? null,
    photoUrl: tgUser?.photo_url ?? null,
  };
}
