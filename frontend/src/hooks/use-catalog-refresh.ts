"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { invalidateCatalogForScreen } from "@/lib/catalog-queries";
import { useNavStore } from "@/store/nav-store";

/** Refetch admin-managed catalog when user navigates to a screen. */
export function useCatalogRefresh() {
  const queryClient = useQueryClient();
  const screen = useNavStore((s) => s.screen);
  const characterId = useNavStore((s) => s.characterId);

  useEffect(() => {
    invalidateCatalogForScreen(queryClient, screen, characterId);
  }, [screen, characterId, queryClient]);
}
