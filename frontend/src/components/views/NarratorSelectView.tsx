"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Mic2 } from "lucide-react";
import { useNavStore } from "@/store/nav-store";
import { useChatsListStore } from "@/store/chats-list-store";
import { useCharacter } from "@/hooks/use-character";
import { useToast } from "@/hooks/use-toast";
import { BackButton } from "@/components/shared/BackButton";
import { ScenarioRowSkeleton } from "@/components/shared/Skeleton";
import { AnimeHeartIcon } from "@/components/icons/CurrencyIcons";
import { characterNarratorsQueryOptions } from "@/lib/catalog-queries";
import { chatService } from "@/services/api";
import { getApiError } from "@/lib/api-client";
import { chatBorderStyle, chatSeparatorStyle } from "@/lib/theme";
import { truncate } from "@/lib/utils";
import { useTranslation } from "@/hooks/use-translation";

export type CharacterNarrator = {
  id: string;
  character_id: string;
  name: string;
  description: string;
  price: number;
  sort_order: number;
};

export function NarratorSelectView() {
  const characterId = useNavStore((s) => s.characterId);
  const scenarioId = useNavStore((s) => s.scenarioId);
  const goBack = useNavStore((s) => s.goBack);
  const openChat = useNavStore((s) => s.openChat);
  const loadChats = useChatsListStore((s) => s.load);
  const upsertChat = useChatsListStore((s) => s.upsertFromDetail);
  const { toast } = useToast();
  const { t } = useTranslation();
  const [starting, setStarting] = useState(false);

  const { character } = useCharacter(characterId);
  const resolvedCharacterId = character?.id ?? characterId;

  const startChat = async (narrator: CharacterNarrator) => {
    const cid = resolvedCharacterId;
    if (!cid || !scenarioId || starting) return;
    setStarting(true);
    try {
      const chat = await chatService.create(cid, scenarioId, narrator.id);
      upsertChat(chat);
      await loadChats();
      openChat(chat.id);
    } catch (err) {
      toast(getApiError(err).message || t("narrator.openError"), "error");
    } finally {
      setStarting(false);
    }
  };

  const { data: narrators = [], isLoading } = useQuery<CharacterNarrator[]>({
    ...characterNarratorsQueryOptions(resolvedCharacterId ?? ""),
    enabled: !!resolvedCharacterId,
  });

  return (
    <div className="mx-auto min-h-screen max-w-lg bg-bg-primary px-4 pb-8 pt-4">
      <header className="mb-5 flex items-center gap-3">
        <BackButton onClick={goBack} />
        <h1 className="flex items-center gap-2 text-lg font-bold text-text-primary">
          <Mic2 className="h-5 w-5 text-accent-light" aria-hidden />
          {t("narrator.title")}
        </h1>
      </header>

      {isLoading ? (
        <div className="overflow-hidden rounded-2xl bg-bg-elevated/60" style={chatBorderStyle}>
          {Array.from({ length: 4 }).map((_, i) => (
            <ScenarioRowSkeleton key={i} />
          ))}
        </div>
      ) : narrators.length === 0 ? (
        <div className="rounded-2xl bg-bg-elevated px-4 py-8 text-center" style={chatBorderStyle}>
          <p className="text-sm font-semibold text-text-primary">{t("narrator.empty")}</p>
          <p className="mt-2 text-xs leading-relaxed text-text-muted">
            {t("narrator.emptyHint")}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl bg-bg-elevated/60" style={chatBorderStyle}>
          {narrators.map((narrator, i) => (
            <motion.button
              key={narrator.id}
              type="button"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              onClick={() => startChat(narrator)}
              disabled={starting}
              className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-bg-elevated active:bg-bg-elevated/80"
              style={i < narrators.length - 1 ? chatSeparatorStyle : undefined}
            >
              <div className="flex h-14 w-[4.5rem] shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-rose-500/30 to-accent/40">
                <AnimeHeartIcon className="h-7 w-7" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="truncate text-[15px] font-semibold text-accent-light">
                    {narrator.name}
                  </h3>
                  {narrator.price > 0 && (
                    <span className="inline-flex shrink-0 items-center gap-1 text-xs font-semibold text-rose-300">
                      {narrator.price}
                      <AnimeHeartIcon className="h-3.5 w-3.5" />
                    </span>
                  )}
                </div>
                <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-text-muted">
                  {truncate(narrator.description || "—", 120)}
                </p>
              </div>
            </motion.button>
          ))}
        </div>
      )}
    </div>
  );
}
