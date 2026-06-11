"use client";



import { useEffect, useState } from "react";

import { useQueryClient } from "@tanstack/react-query";

import { authService } from "@/services/api";

import { prefetchCatalogQueries } from "@/lib/catalog-queries";

import { getApiError } from "@/lib/api-client";

import type { BanInfo } from "@/features/auth/BannedScreen";

import { useAuthStore } from "@/store/auth-store";

import { useUserStore } from "@/store/user-store";



function prefetchCatalog(queryClient: ReturnType<typeof useQueryClient>) {

  prefetchCatalogQueries(queryClient);

}



function banFromApiError(apiErr: ReturnType<typeof getApiError>): BanInfo {

  return {

    message: apiErr.message,

    ban_reason: apiErr.ban_reason,

    banned_until: apiErr.banned_until,

  };

}



function isBannedError(err: unknown): boolean {

  return getApiError(err).code === "ACCOUNT_BANNED";

}



export function useTelegramAuth() {

  const queryClient = useQueryClient();

  const { setTokens, clearAuth, isAuthenticated, isLoading, setLoading } = useAuthStore();

  const { setUser } = useUserStore();

  const [error, setError] = useState<string | null>(null);

  const [banInfo, setBanInfo] = useState<BanInfo | null>(null);



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

              prefetchCatalog(queryClient);

              setLoading(false);

              return;

            } catch (err) {

              if (isBannedError(err)) {

                setBanInfo(banFromApiError(getApiError(err)));

                clearAuth();

                setLoading(false);

                return;

              }

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

              prefetchCatalog(queryClient);

              setLoading(false);

              return;

            } catch (err) {

              if (isBannedError(err)) {

                setBanInfo(banFromApiError(getApiError(err)));

                clearAuth();

                setLoading(false);

                return;

              }

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

        prefetchCatalog(queryClient);

      } catch (err) {

        if (isBannedError(err)) {

          setBanInfo(banFromApiError(getApiError(err)));

          clearAuth();

        } else {

          setError(getApiError(err).message || "Ошибка авторизации");

          clearAuth();

        }

      } finally {

        setLoading(false);

      }

    }



    init();

  }, [setTokens, clearAuth, setUser, setLoading, queryClient]);



  return { isAuthenticated, isLoading, error, banInfo };

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


