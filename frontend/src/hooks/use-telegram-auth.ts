"use client";

import { useEffect, useState } from "react";
import { authService } from "@/services/api";
import { useAuthStore } from "@/store/auth-store";
import { useUserStore } from "@/store/user-store";

export function useTelegramAuth() {
  const { setTokens, clearAuth, isAuthenticated, isLoading, setLoading } = useAuthStore();
  const { setUser } = useUserStore();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function init() {
      try {
        if (typeof window === "undefined") return;

        const tg = (window as unknown as { Telegram?: { WebApp?: TelegramWebApp } }).Telegram?.WebApp;
        if (tg) {
          tg.ready();
          tg.expand();
        }

        const initData = tg?.initData;
        if (!initData) {
          const existingToken = localStorage.getItem("access_token");
          if (existingToken) {
            try {
              const user = await authService.getMe();
              setUser(user);
              setLoading(false);
              return;
            } catch {
              localStorage.removeItem("access_token");
              localStorage.removeItem("refresh_token");
            }
          }
          const isLocalDev =
            window.location.hostname === "localhost" ||
            window.location.hostname === "127.0.0.1";
          if (isLocalDev) {
            try {
              const tokens = await authService.authenticateDev();
              setTokens(tokens.access_token, tokens.refresh_token);
              const user = await authService.getMe();
              setUser(user);
              setLoading(false);
              return;
            } catch (err) {
              setError(
                err instanceof Error
                  ? err.message
                  : "Dev-вход не удался. Откройте через Telegram или /start в боте."
              );
            }
          }
          setLoading(false);
          return;
        }

        const tokens = await authService.authenticateTelegram(initData);
        setTokens(tokens.access_token, tokens.refresh_token);
        const user = await authService.getMe();
        setUser(user);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Ошибка авторизации");
        clearAuth();
      } finally {
        setLoading(false);
      }
    }

    init();
  }, [setTokens, clearAuth, setUser, setLoading]);

  return { isAuthenticated, isLoading, error };
}

interface TelegramWebApp {
  initData: string;
  ready: () => void;
  expand: () => void;
  close: () => void;
  MainButton: {
    text: string;
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
  };
  themeParams: Record<string, string>;
  colorScheme: "light" | "dark";
}
