"use client";

import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/constants";
import { characterService } from "@/services/api";
import type { Character } from "@/store/character-store";
import { useCharacterStore } from "@/store/character-store";

export function useCharacter(characterId: string | null) {
  const cached = useCharacterStore((s) =>
    characterId ? s.characters.find((c) => c.id === characterId) : undefined
  );

  const query = useQuery({
    queryKey: QUERY_KEYS.character(characterId ?? ""),
    queryFn: () => characterService.resolve(characterId!),
    enabled: !!characterId,
    retry: 1,
    staleTime: 60_000,
  });

  const character: Character | null | undefined =
    (query.data as Character | undefined) ?? cached ?? null;

  const isLoading =
    !!characterId && query.isLoading && !character;

  return { character, isLoading, isError: query.isError && !character };
}
