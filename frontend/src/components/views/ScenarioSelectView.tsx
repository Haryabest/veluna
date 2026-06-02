"use client";

import { motion } from "framer-motion";
import { useNavStore } from "@/store/nav-store";
import { getMockCharacter, MOCK_SCENARIOS } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export function ScenarioSelectView() {
  const characterId = useNavStore((s) => s.characterId);
  const goBack = useNavStore((s) => s.goBack);
  const openChatForCharacter = useNavStore((s) => s.openChatForCharacter);

  const character = characterId ? getMockCharacter(characterId) : null;

  return (
    <div className="mx-auto min-h-screen max-w-lg px-4 pb-8 pt-4">
      <header className="mb-5 flex items-center gap-3">
        <button
          type="button"
          onClick={goBack}
          aria-label="Назад"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full glass-strong text-lg active:scale-95"
        >
          ←
        </button>
        <div>
          <h1 className="text-lg font-bold">Выбор сценария</h1>
          {character && (
            <p className="text-sm text-text-muted">с {character.name}</p>
          )}
        </div>
      </header>

      <div className="space-y-3">
        {MOCK_SCENARIOS.map((scenario, i) => (
          <motion.button
            key={scenario.id}
            type="button"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
            onClick={() => characterId && openChatForCharacter(characterId)}
            className={cn(
              "glass group w-full overflow-hidden rounded-2xl text-left transition-all",
              "hover:shadow-glow active:scale-[0.98]"
            )}
          >
            <div className="relative aspect-[16/9] overflow-hidden">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={scenario.imageUrl}
                alt={scenario.title}
                className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-bg-primary/90 via-transparent to-transparent" />
              <div className="absolute inset-x-0 bottom-0 p-4">
                <h3 className="font-bold">{scenario.title}</h3>
                <p className="mt-0.5 text-sm text-text-secondary">{scenario.description}</p>
              </div>
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
