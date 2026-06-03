"use client";

import { useEffect, useState } from "react";
import {
  getTelegramDisplayName,
  getTelegramUser,
  type TelegramUser,
} from "@/lib/telegram-webapp";

export function useTelegramUser() {
  const [tgUser, setTgUser] = useState<TelegramUser | null>(null);

  useEffect(() => {
    setTgUser(getTelegramUser());
  }, []);

  return {
    tgUser,
    displayName: getTelegramDisplayName(tgUser),
    username: tgUser?.username ?? null,
    photoUrl: tgUser?.photo_url ?? null,
  };
}
