"use client";

import { useQuery } from "@tanstack/react-query";
import { characterService } from "@/services/api";
import { CharacterCard } from "@/components/entities/CharacterCard";
import { CharacterCardSkeleton } from "@/components/shared/Skeleton";
import { CurrencyBar } from "@/components/widgets/CurrencyBar";
import { MOCK_CHARACTERS } from "@/lib/mock-data";
import { QUERY_KEYS } from "@/lib/constants";
import type { Character } from "@/store/character-store";

export default function HomePage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: QUERY_KEYS.characters,
    queryFn: () => characterService.list(),
    retry: false,
  });

  const characters: Character[] =
    !isError && data?.items?.length ? data.items : MOCK_CHARACTERS;

  return (
    <div className="mx-auto max-w-lg px-4 pb-28 pt-5">
      <CurrencyBar stars={25} />

      <section className="mt-5">
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-widest text-text-muted">
          Персонажи
        </h2>

        <div className="grid grid-cols-2 gap-3">
          {isLoading
            ? Array.from({ length: 4 }).map((_, i) => <CharacterCardSkeleton key={i} />)
            : characters.map((character, i) => (
                <CharacterCard key={character.id} character={character} index={i} />
              ))}
        </div>
      </section>
    </div>
  );
}
