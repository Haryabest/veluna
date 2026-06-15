import type { QueryClient } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/constants";
import type { AppLocale } from "@/lib/i18n/translations";

const CHATS_CACHE_KEY = "veluna_chats_cache_v2";

/** Refetch catalog and chats after user switches UI language. */
export function onLocaleChanged(queryClient: QueryClient, _locale: AppLocale) {
  if (typeof window !== "undefined") {
    try {
      localStorage.removeItem(CHATS_CACHE_KEY);
    } catch {
      /* ignore */
    }
  }

  void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.user });
  void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.chats });
  void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.shopProducts });

  void queryClient.invalidateQueries({
    predicate: (query) => {
      const key = query.queryKey[0];
      return (
        key === "characters" ||
        key === "character" ||
        key === "character-scenarios" ||
        key === "character-narrators" ||
        key === "chat"
      );
    },
  });
}
