"use client";

import { useEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Mic2, Sparkles } from "lucide-react";
import { AnimeHeartIcon } from "@/components/icons/CurrencyIcons";
import { CHAT_BORDER, chatSeparatorStyle } from "@/lib/theme";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/hooks/use-translation";
import type { CharacterNarrator } from "@/components/views/NarratorSelectView";
import type { CharacterScenario } from "@/store/character-store";

export interface ChatMenuAnchor {
  top: number;
  left: number;
  width: number;
}

interface ChatSettingsMenuProps {
  open: boolean;
  anchor: ChatMenuAnchor | null;
  scenarios: CharacterScenario[];
  narrators: CharacterNarrator[];
  currentScenarioId: string | null;
  currentNarratorId: string | null;
  loadingScenarios?: boolean;
  loadingNarrators?: boolean;
  switching?: boolean;
  onClose: () => void;
  onSelectScenario: (scenarioId: string) => void;
  onSelectNarrator: (narratorId: string) => void;
}

export function ChatSettingsMenu({
  open,
  anchor,
  scenarios,
  narrators,
  currentScenarioId,
  currentNarratorId,
  loadingScenarios,
  loadingNarrators,
  switching,
  onClose,
  onSelectScenario,
  onSelectNarrator,
}: ChatSettingsMenuProps) {
  const { t } = useTranslation();

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (typeof document === "undefined") return null;

  const menuTop = anchor ? Math.min(anchor.top + 8, window.innerHeight - 420) : 0;
  const menuRight = anchor
    ? Math.min(Math.max(window.innerWidth - anchor.left - anchor.width, 12), window.innerWidth - 12)
    : 12;
  const menuWidth = Math.min(300, window.innerWidth - 24);

  return createPortal(
    <AnimatePresence>
      {open && anchor && (
        <>
          <motion.button
            type="button"
            aria-label={t("common.closeMenu")}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[80] bg-black/40"
            onClick={onClose}
          />
          <motion.div
            role="menu"
            initial={{ opacity: 0, scale: 0.92, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.92, y: -8 }}
            transition={{ type: "spring", stiffness: 420, damping: 28 }}
            className="fixed z-[85] max-h-[min(420px,72vh)] overflow-hidden overflow-y-auto rounded-2xl bg-bg-elevated/95 py-1 backdrop-blur-xl"
            style={{
              top: menuTop,
              right: menuRight,
              width: menuWidth,
              border: `1px solid ${CHAT_BORDER}`,
            }}
          >
            <p className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">
              <Sparkles className="h-3.5 w-3.5 text-accent-light" aria-hidden />
              {t("chat.scenario")}
            </p>
            {loadingScenarios ? (
              <p className="px-4 py-4 text-center text-sm text-text-muted">{t("common.loading")}</p>
            ) : scenarios.length === 0 ? (
              <p className="px-4 py-4 text-center text-sm text-text-muted">{t("chat.noScenarios")}</p>
            ) : (
              scenarios.map((scenario, i) => {
                const active = scenario.id === currentScenarioId;
                return (
                  <button
                    key={scenario.id}
                    type="button"
                    role="menuitem"
                    disabled={switching}
                    onClick={() => onSelectScenario(scenario.id)}
                    className={cn(
                      "flex w-full items-center gap-3 px-4 py-3 text-left text-sm transition-colors",
                      active ? "bg-accent/15 text-accent-light" : "text-text-primary hover:bg-bg-elevated/80",
                      switching && "opacity-60"
                    )}
                    style={i < scenarios.length - 1 ? chatSeparatorStyle : undefined}
                  >
                    <span className="min-w-0 flex-1 truncate font-medium">{scenario.title}</span>
                    {active && <Check className="h-4 w-4 shrink-0 text-accent-light" aria-hidden />}
                  </button>
                );
              })
            )}

            <div className="my-1 h-px bg-white/5" />

            <p className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">
              <Mic2 className="h-3.5 w-3.5 text-rose-300" aria-hidden />
              {t("chat.narrator")}
            </p>
            {loadingNarrators ? (
              <p className="px-4 py-4 text-center text-sm text-text-muted">{t("common.loading")}</p>
            ) : narrators.length === 0 ? (
              <p className="px-4 py-4 text-center text-sm text-text-muted">{t("chat.noNarrators")}</p>
            ) : (
              narrators.map((narrator, i) => {
                const active = narrator.id === currentNarratorId;
                return (
                  <button
                    key={narrator.id}
                    type="button"
                    role="menuitem"
                    disabled={switching}
                    onClick={() => onSelectNarrator(narrator.id)}
                    className={cn(
                      "flex w-full items-center gap-3 px-4 py-3 text-left text-sm transition-colors",
                      active ? "bg-accent/15 text-accent-light" : "text-text-primary hover:bg-bg-elevated/80",
                      switching && "opacity-60"
                    )}
                    style={i < narrators.length - 1 ? chatSeparatorStyle : undefined}
                  >
                    <span className="flex min-w-0 flex-1 items-center gap-1.5 truncate font-medium">
                      <span className="truncate">{narrator.name}</span>
                      {narrator.price > 0 && (
                        <span className="inline-flex shrink-0 items-center gap-0.5 text-xs text-rose-300">
                          {narrator.price}
                          <AnimeHeartIcon className="h-3 w-3" />
                        </span>
                      )}
                    </span>
                    {active && <Check className="h-4 w-4 shrink-0 text-accent-light" aria-hidden />}
                  </button>
                );
              })
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>,
    document.body
  );
}

/** @deprecated use ChatSettingsMenu */
export const ChatScenarioMenu = ChatSettingsMenu;
