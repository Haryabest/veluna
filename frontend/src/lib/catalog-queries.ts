import { QUERY_KEYS } from "@/lib/constants";
import { balanceService, characterService, shopService } from "@/services/api";
import type { QueryClient } from "@tanstack/react-query";

/** Admin-managed catalog: always refetch when screen opens or app returns to foreground. */
const catalogQueryDefaults = {
  staleTime: 0,
  refetchOnMount: "always" as const,
  refetchOnWindowFocus: true,
  retry: 2,
};

export const shopProductsQueryOptions = {
  queryKey: QUERY_KEYS.shopProducts,
  queryFn: () => shopService.listProducts(),
  ...catalogQueryDefaults,
};

export const charactersListQueryOptions = {
  queryKey: QUERY_KEYS.characters(1),
  queryFn: () => characterService.list(1),
  ...catalogQueryDefaults,
};

export function characterQueryOptions(characterId: string) {
  return {
    queryKey: QUERY_KEYS.character(characterId),
    queryFn: () => characterService.resolve(characterId),
    enabled: !!characterId,
    ...catalogQueryDefaults,
  };
}

export function characterScenariosQueryOptions(characterId: string) {
  return {
    queryKey: QUERY_KEYS.characterScenarios(characterId),
    queryFn: () => characterService.listScenarios(characterId),
    enabled: !!characterId,
    ...catalogQueryDefaults,
  };
}

export function characterNarratorsQueryOptions(characterId: string) {
  return {
    queryKey: QUERY_KEYS.characterNarrators(characterId),
    queryFn: () => characterService.listNarrators(characterId),
    enabled: !!characterId,
    ...catalogQueryDefaults,
  };
}

export const balanceQueryOptions = {
  queryKey: QUERY_KEYS.balance,
  queryFn: () => balanceService.get(),
  ...catalogQueryDefaults,
};

export function prefetchCatalogQueries(queryClient: QueryClient) {
  void queryClient.prefetchQuery(shopProductsQueryOptions);
  void queryClient.prefetchQuery(charactersListQueryOptions);
}

export function refreshAllCatalogQueries(queryClient: QueryClient) {
  void queryClient.refetchQueries({
    predicate: (query) => {
      const key = query.queryKey[0];
      return (
        key === "characters" ||
        key === "character" ||
        key === "character-scenarios" ||
        key === "character-narrators" ||
        key === "shop"
      );
    },
    type: "active",
  });
  void queryClient.refetchQueries({ queryKey: QUERY_KEYS.balance, type: "active" });
}

/** @deprecated use refreshAllCatalogQueries */
export function invalidateAllCatalogQueries(queryClient: QueryClient) {
  refreshAllCatalogQueries(queryClient);
}

export function invalidateCatalogForScreen(
  queryClient: QueryClient,
  screen: string,
  characterId: string | null
) {
  switch (screen) {
    case "home":
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.characters(1) });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.balance });
      break;
    case "profile":
    case "history":
    case "topup":
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.balance });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.financeStats });
      break;
    case "shop":
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.shopProducts });
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.balance });
      break;
    case "character":
      if (characterId) {
        void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.characters(1) });
        void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.character(characterId) });
      }
      break;
    case "scenarios":
      if (characterId) {
        void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.character(characterId) });
        void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.characterScenarios(characterId) });
      }
      break;
    case "narrators":
      if (characterId) {
        void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.characterNarrators(characterId) });
      }
      break;
    default:
      break;
  }
}
