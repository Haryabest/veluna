"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { useNavStore } from "@/store/nav-store";
import { useCharacter } from "@/hooks/use-character";
import { BackButton } from "@/components/shared/BackButton";
import { ScenarioRowSkeleton } from "@/components/shared/Skeleton";
import { characterScenariosQueryOptions } from "@/lib/catalog-queries";
import { chatBorderStyle, chatSeparatorStyle } from "@/lib/theme";
import { truncate } from "@/lib/utils";
import { useOpenNarrators } from "@/hooks/use-catalog-navigation";
import type { CharacterScenario } from "@/store/character-store";
import { useTranslation } from "@/hooks/use-translation";

function scenarioDescription(scenario: CharacterScenario): string {
  const parts = [scenario.story, scenario.communication_style].filter(Boolean);
  return truncate(parts.join(" · ") || scenario.opening_message || "—", 120);
}

export function ScenarioSelectView() {
  const characterId = useNavStore((s) => s.characterId);
  const goBack = useNavStore((s) => s.goBack);
  const openNarrators = useOpenNarrators();
  const { t } = useTranslation();

  const { character } = useCharacter(characterId);
  const resolvedCharacterId = character?.id ?? characterId;

  const { data: scenarios = [], isLoading } = useQuery<CharacterScenario[]>({
    ...characterScenariosQueryOptions(resolvedCharacterId ?? ""),
    enabled: !!resolvedCharacterId,
  });

  const thumbUrl = character?.preview_url || character?.avatar_url;

  return (
    <div className="mx-auto min-h-screen max-w-lg bg-bg-primary px-4 pb-8 pt-4">
      <header className="mb-5 flex items-center gap-3">
        <BackButton onClick={goBack} />
        <h1 className="flex items-center gap-2 text-lg font-bold text-text-primary">
          <Sparkles className="h-5 w-5 text-accent-light" aria-hidden />
          {t("scenario.title")}
        </h1>
      </header>

      {isLoading ? (
        <div className="overflow-hidden rounded-2xl bg-bg-elevated/60" style={chatBorderStyle}>
          {Array.from({ length: 4 }).map((_, i) => (
            <ScenarioRowSkeleton key={i} />
          ))}
        </div>
      ) : scenarios.length === 0 ? (
        <div className="rounded-2xl bg-bg-elevated px-4 py-8 text-center" style={chatBorderStyle}>
          <p className="text-sm font-semibold text-text-primary">{t("scenario.empty")}</p>
          <p className="mt-2 text-xs leading-relaxed text-text-muted">
            {t("scenario.emptyHint")}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl bg-bg-elevated/60" style={chatBorderStyle}>
          {scenarios.map((scenario, i) => (
            <motion.button
              key={scenario.id}
              type="button"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              onClick={() => openNarrators(scenario.id)}
              className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-bg-elevated active:bg-bg-elevated/80"
              style={i < scenarios.length - 1 ? chatSeparatorStyle : undefined}
            >
              {thumbUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={thumbUrl}
                  alt=""
                  className="h-14 w-[4.5rem] shrink-0 rounded-xl object-cover"
                />
              ) : (
                <div className="flex h-14 w-[4.5rem] shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-accent-deep to-accent/50 text-xl">
                  ✨
                </div>
              )}
              <div className="min-w-0 flex-1">
                <h3 className="truncate text-[15px] font-semibold text-accent-light">
                  {scenario.title}
                </h3>
                <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-text-muted">
                  {scenarioDescription(scenario)}
                </p>
              </div>
            </motion.button>
          ))}
        </div>
      )}
    </div>
  );
}
