"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { characterQueryOptions } from "@/lib/catalog-queries";
import type { Character } from "@/store/character-store";
import { useCharacterStore } from "@/store/character-store";

export function useCharacter(characterId: string | null) {
  const setCharacters = useCharacterStore((s) => s.setCharacters);
  const cached = useCharacterStore((s) =>
    characterId ? s.characters.find((c) => c.id === characterId) : undefined
  );

  const query = useQuery(characterQueryOptions(characterId ?? ""));

  const character: Character | null | undefined =
    query.isSuccess && query.data
      ? (query.data as Character)
      : query.isLoading
        ? (cached ?? null)
        : ((query.data as Character | undefined) ?? cached ?? null);

  useEffect(() => {
    const fresh = query.data as Character | undefined;
    if (!fresh?.id) return;
    const list = useCharacterStore.getState().characters;
    if (list.length === 0) return;
    const prev = list.find((c) => c.id === fresh.id);
    if (!prev) return;
    if (
      prev.name === fresh.name &&
      prev.subtitle === fresh.subtitle &&
      prev.description === fresh.description &&
      prev.avatar_url === fresh.avatar_url &&
      prev.preview_url === fresh.preview_url
    ) {
      return;
    }
    setCharacters(list.map((c) => (c.id === fresh.id ? { ...c, ...fresh } : c)));
  }, [query.data, setCharacters]);

  const isLoading =
    !!characterId && query.isLoading && !character;

  return { character, isLoading, isError: query.isError && !character };
}
