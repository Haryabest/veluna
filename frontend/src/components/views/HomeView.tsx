"use client";

import { CharacterCard } from "@/components/entities/CharacterCard";
import { CurrencyBar } from "@/components/widgets/CurrencyBar";
import { MOCK_CHARACTERS } from "@/lib/mock-data";

export function HomeView() {
  const characters = MOCK_CHARACTERS;

  return (
    <div className="mx-auto max-w-lg px-4 pt-5">
      <CurrencyBar hearts={25} />

      <section className="mt-5">
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-widest text-text-muted">
          Персонажи
        </h2>

        <div className="grid grid-cols-2 gap-3">
          {characters.map((character, i) => (
            <CharacterCard key={character.id} character={character} index={i} />
          ))}
        </div>
      </section>
    </div>
  );
}
