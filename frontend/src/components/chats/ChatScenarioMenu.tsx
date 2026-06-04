"use client";

import { useEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Sparkles } from "lucide-react";
import { CHAT_BORDER, chatSeparatorStyle } from "@/lib/theme";
import { cn } from "@/lib/utils";
import type { CharacterScenario } from "@/store/character-store";

export interface ChatMenuAnchor {
  top: number;
  left: number;
  width: number;
}

interface ChatScenarioMenuProps {
  open: boolean;
  anchor: ChatMenuAnchor | null;
  scenarios: CharacterScenario[];
  currentScenarioId: string | null;
  loading?: boolean;
  switching?: boolean;
  onClose: () => void;
  onSelect: (scenarioId: string) => void;
}

export function ChatScenarioMenu({
  open,
  anchor,
  scenarios,
  currentScenarioId,
  loading,
  switching,
  onClose,
  onSelect,
}: ChatScenarioMenuProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (typeof document === "undefined") return null;

  const menuTop = anchor ? Math.min(anchor.top + 8, window.innerHeight - 320) : 0;
  const menuRight = anchor
    ? Math.min(Math.max(window.innerWidth - anchor.left - anchor.width, 12), window.innerWidth - 12)
    : 12;
  const menuWidth = Math.min(280, window.innerWidth - 24);

  return createPortal(
    <AnimatePresence>
      {open && anchor && (
        <>
          <motion.button
            type="button"
            aria-label="Закрыть меню"
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
            className="fixed z-[85] max-h-[min(360px,70vh)] overflow-hidden overflow-y-auto rounded-2xl bg-bg-elevated/95 py-1 backdrop-blur-xl"
            style={{
              top: menuTop,
              right: menuRight,
              width: menuWidth,
              border: `1px solid ${CHAT_BORDER}`,
            }}
          >
            <p className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">
              <Sparkles className="h-3.5 w-3.5 text-accent-light" aria-hidden />
              Сценарий
            </p>
            {loading ? (
              <p className="px-4 py-6 text-center text-sm text-text-muted">Загрузка…</p>
            ) : scenarios.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-text-muted">Сценариев нет</p>
            ) : (
              scenarios.map((scenario, i) => {
                const active = scenario.id === currentScenarioId;
                return (
                  <button
                    key={scenario.id}
                    type="button"
                    role="menuitem"
                    disabled={switching}
                    onClick={() => onSelect(scenario.id)}
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
          </motion.div>
        </>
      )}
    </AnimatePresence>,
    document.body
  );
}
