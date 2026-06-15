"use client";

import { useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { CharacterCard } from "@/components/entities/CharacterCard";
import { CharacterCardSkeleton } from "@/components/shared/Skeleton";
import { CurrencyBar } from "@/components/widgets/CurrencyBar";
import { charactersListQueryOptions, balanceQueryOptions } from "@/lib/catalog-queries";
import type { Character } from "@/store/character-store";
import { useCharacterStore } from "@/store/character-store";
import { useTranslation } from "@/hooks/use-translation";

function sortCharacters(list: Character[]): Character[] {
  return [...list].sort((a, b) => a.sort_order - b.sort_order);
}

export function HomeView() {
  const { t } = useTranslation();
  const setCharacters = useCharacterStore((s) => s.setCharacters);

  const { data: balance } = useQuery(balanceQueryOptions);

  const { data, isFetching, isError } = useQuery(charactersListQueryOptions());

  const characters: Character[] = useMemo(() => {
    const items = data?.items;
    if (Array.isArray(items) && items.length > 0) {
      return sortCharacters(items as Character[]);
    }
    return [];
  }, [data]);

  useEffect(() => {
    const items = data?.items;
    if (!Array.isArray(items)) return;
    setCharacters(sortCharacters(items as Character[]));
  }, [data, setCharacters]);

  return (
    <div className="mx-auto max-w-lg px-4 pt-5">
      <CurrencyBar gems={balance?.gems} hearts={balance?.credits} />

      <section className="mt-5">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-text-muted">
            {t("home.characters")}
          </h2>
          {isFetching && (
            <span className="text-[10px] text-text-muted">{t("home.refreshing")}</span>
          )}
          {isError && (
            <span className="text-[10px] text-amber-400/90">{t("home.loadError")}</span>
          )}
        </div>

        {!isFetching && characters.length === 0 ? (
          <p className="py-12 text-center text-sm text-text-muted">{t("home.empty")}</p>
        ) : isFetching && characters.length === 0 ? (
          <div className="grid grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <CharacterCardSkeleton key={i} />
            ))}
          </div>
        ) : (
        <div className="grid grid-cols-2 gap-3">
          {characters.map((character, i) => (
            <CharacterCard key={character.id} character={character} index={i} />
          ))}
        </div>
        )}
      </section>
    </div>
  );
}
