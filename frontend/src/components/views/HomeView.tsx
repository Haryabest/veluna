"use client";

import { useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { CharacterCard } from "@/components/entities/CharacterCard";
import { CharacterCardSkeleton } from "@/components/shared/Skeleton";
import { CurrencyBar } from "@/components/widgets/CurrencyBar";
import { QUERY_KEYS } from "@/lib/constants";
import { characterService, balanceService } from "@/services/api";
import type { Character } from "@/store/character-store";
import { useCharacterStore } from "@/store/character-store";

function sortCharacters(list: Character[]): Character[] {
  return [...list].sort((a, b) => a.sort_order - b.sort_order);
}

export function HomeView() {
  const setCharacters = useCharacterStore((s) => s.setCharacters);

  const { data: balance } = useQuery({
    queryKey: QUERY_KEYS.balance,
    queryFn: () => balanceService.get(),
    staleTime: 15_000,
  });

  const { data, isFetching, isError } = useQuery({
    queryKey: QUERY_KEYS.characters(1),
    queryFn: () => characterService.list(1),
    retry: 1,
    staleTime: 30_000,
  });

  const characters: Character[] = useMemo(() => {
    const items = data?.items;
    if (Array.isArray(items) && items.length > 0) {
      return sortCharacters(items as Character[]);
    }
    return [];
  }, [data]);

  useEffect(() => {
    if (Array.isArray(data?.items) && data.items.length > 0) {
      setCharacters(sortCharacters(data.items as Character[]));
    }
  }, [data, setCharacters]);

  return (
    <div className="mx-auto max-w-lg px-4 pt-5">
      <CurrencyBar gems={balance?.gems} hearts={balance?.credits} />

      <section className="mt-5">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-text-muted">
            Персонажи
          </h2>
          {isFetching && characters.length === 0 && (
            <span className="text-[10px] text-text-muted">обновление…</span>
          )}
          {isError && (
            <span className="text-[10px] text-amber-400/90">не удалось загрузить</span>
          )}
        </div>

        {!isFetching && characters.length === 0 ? (
          <p className="py-12 text-center text-sm text-text-muted">Персонажи пока недоступны</p>
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
