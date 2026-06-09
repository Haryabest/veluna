"use client";

import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/constants";
import { refreshAllCatalogQueries } from "@/lib/catalog-queries";
import { useNavStore } from "@/store/nav-store";

export function useOpenShop() {
  const queryClient = useQueryClient();
  const openShop = useNavStore((s) => s.openShop);

  return useCallback(() => {
    refreshAllCatalogQueries(queryClient);
    openShop();
  }, [openShop, queryClient]);
}

export function useOpenCharacter() {
  const queryClient = useQueryClient();
  const openCharacter = useNavStore((s) => s.openCharacter);

  return useCallback(
    (characterId: string) => {
      refreshAllCatalogQueries(queryClient);
      openCharacter(characterId);
    },
    [openCharacter, queryClient]
  );
}

export function useOpenScenarios() {
  const queryClient = useQueryClient();
  const openScenarios = useNavStore((s) => s.openScenarios);
  const characterId = useNavStore((s) => s.characterId);

  return useCallback(() => {
    if (characterId) {
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.characterScenarios(characterId) });
    }
    openScenarios();
  }, [characterId, openScenarios, queryClient]);
}

export function useOpenNarrators() {
  const queryClient = useQueryClient();
  const openNarrators = useNavStore((s) => s.openNarrators);
  const characterId = useNavStore((s) => s.characterId);

  return useCallback(
    (scenarioId: string) => {
      if (characterId) {
        void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.characterNarrators(characterId) });
      }
      openNarrators(scenarioId);
    },
    [characterId, openNarrators, queryClient]
  );
}

export function useSetTab() {
  const queryClient = useQueryClient();
  const setTab = useNavStore((s) => s.setTab);
  const tab = useNavStore((s) => s.tab);

  return useCallback(
    (nextTab: Parameters<typeof setTab>[0]) => {
      if (nextTab === tab || nextTab === "home") {
        refreshAllCatalogQueries(queryClient);
      }
      setTab(nextTab);
    },
    [setTab, queryClient, tab]
  );
}
