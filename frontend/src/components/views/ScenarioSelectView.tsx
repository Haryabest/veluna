"use client";

import { motion } from "framer-motion";
import { useNavStore } from "@/store/nav-store";
import { getMockCharacter, MOCK_SCENARIOS } from "@/lib/mock-data";
import { BackButton } from "@/components/shared/BackButton";
import { ListPanel } from "@/components/shared/ListPanel";
import { chatSeparatorStyle } from "@/lib/theme";

export function ScenarioSelectView() {
  const characterId = useNavStore((s) => s.characterId);
  const goBack = useNavStore((s) => s.goBack);
  const openChatForCharacter = useNavStore((s) => s.openChatForCharacter);

  const character = characterId ? getMockCharacter(characterId) : null;

  return (
    <div className="mx-auto min-h-screen max-w-lg px-4 pb-8 pt-4">
      <header className="mb-4 flex items-center gap-3">
        <BackButton onClick={goBack} />
        <div>
          <h1 className="text-lg font-bold">Выбор сценария</h1>
          {character && <p className="text-sm text-text-muted">с {character.name}</p>}
        </div>
      </header>

      <ListPanel>
        {MOCK_SCENARIOS.map((scenario, i) => (
          <motion.button
            key={scenario.id}
            type="button"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            onClick={() => characterId && openChatForCharacter(characterId)}
            className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-bg-elevated/60 active:bg-bg-elevated/80"
            style={i < MOCK_SCENARIOS.length - 1 ? chatSeparatorStyle : undefined}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={scenario.imageUrl}
              alt=""
              className="h-14 w-20 shrink-0 rounded-lg object-cover"
            />
            <div className="min-w-0 flex-1">
              <h3 className="truncate text-sm font-semibold">{scenario.title}</h3>
              <p className="mt-0.5 line-clamp-2 text-xs text-text-muted">{scenario.description}</p>
            </div>
          </motion.button>
        ))}
      </ListPanel>
    </div>
  );
}
