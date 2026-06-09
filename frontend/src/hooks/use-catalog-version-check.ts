"use client";

import { useCallback, useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { refreshAllCatalogQueries } from "@/lib/catalog-queries";
import { catalogService } from "@/services/api";
import { useNavStore } from "@/store/nav-store";

/** If admin changed catalog, refetch once (no polling). */
export function useCatalogVersionCheck() {
  const queryClient = useQueryClient();
  const screen = useNavStore((s) => s.screen);
  const lastVersion = useRef<number | null>(null);

  const check = useCallback(async () => {
    try {
      const version = await catalogService.getVersion();
      if (lastVersion.current !== null && version !== lastVersion.current) {
        refreshAllCatalogQueries(queryClient);
      }
      lastVersion.current = version;
    } catch {
      /* backend offline or old deploy */
    }
  }, [queryClient]);

  useEffect(() => {
    void check();
  }, [check, screen]);

  useEffect(() => {
    const onWake = () => {
      if (document.visibilityState === "visible") {
        void check();
      }
    };

    document.addEventListener("visibilitychange", onWake);
    window.addEventListener("focus", onWake);
    window.addEventListener("pageshow", onWake);

    const tg = (
      window as unknown as { Telegram?: { WebApp?: { onEvent?: (e: string, cb: () => void) => void } } }
    ).Telegram?.WebApp;
    tg?.onEvent?.("viewportChanged", onWake);

    return () => {
      document.removeEventListener("visibilitychange", onWake);
      window.removeEventListener("focus", onWake);
      window.removeEventListener("pageshow", onWake);
    };
  }, [check]);
}
