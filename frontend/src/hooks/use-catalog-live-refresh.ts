"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { refreshAllCatalogQueries } from "@/lib/catalog-queries";

/** Refetch catalog when user returns to Mini App (fallback if version API unavailable). */
export function useCatalogLiveRefresh() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const refresh = () => {
      if (document.visibilityState === "visible") {
        refreshAllCatalogQueries(queryClient);
      }
    };

    document.addEventListener("visibilitychange", refresh);
    window.addEventListener("focus", refresh);
    window.addEventListener("pageshow", refresh);

    return () => {
      document.removeEventListener("visibilitychange", refresh);
      window.removeEventListener("focus", refresh);
      window.removeEventListener("pageshow", refresh);
    };
  }, [queryClient]);
}
