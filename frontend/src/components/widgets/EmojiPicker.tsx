"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/hooks/use-translation";
import type { TranslationKey } from "@/lib/i18n/translations";

import { CHAT_BORDER } from "@/lib/theme";

const EMOJI_CATEGORIES: { id: string; labelKey: TranslationKey; icon: string; emojis: string[] }[] = [
  {
    id: "smileys",
    labelKey: "emoji.smiles",
    icon: "😀",
    emojis: [
      "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂", "🙂", "😊",
      "😇", "🥰", "😍", "🤩", "😘", "😗", "😚", "😙", "🥲", "😋",
      "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🫢", "🤫", "🤔",
      "😐", "😑", "😶", "🫥", "😏", "😒", "🙄", "😬", "😮‍💨", "🤥",
    ],
  },
  {
    id: "hearts",
    labelKey: "emoji.hearts",
    icon: "❤️",
    emojis: [
      "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
      "❤️‍🔥", "❤️‍🩹", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟",
      "♥️", "🫶", "😻", "💑", "💏", "🌹", "✨", "💫", "⭐", "🌟",
    ],
  },
  {
    id: "gestures",
    labelKey: "emoji.gestures",
    icon: "👋",
    emojis: [
      "👋", "🤚", "🖐️", "✋", "🖖", "👌", "🤌", "🤏", "✌️", "🤞",
      "🫰", "🤟", "🤘", "🤙", "👈", "👉", "👆", "👇", "☝️", "👍",
      "👎", "✊", "👊", "🤛", "🤜", "👏", "🙌", "🫶", "🤝", "🙏",
    ],
  },
  {
    id: "animals",
    labelKey: "emoji.animals",
    icon: "🐱",
    emojis: [
      "🐱", "🐶", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯",
      "🦁", "🐮", "🐷", "🐸", "🐵", "🐔", "🐧", "🐦", "🦋", "🐝",
      "🌸", "🌺", "🌷", "🌹", "🍀", "🌙", "☀️", "🌈", "❄️", "🔥",
    ],
  },
];

interface EmojiPickerProps {
  open: boolean;
  onClose: () => void;
  onSelect: (emoji: string) => void;
}

export function EmojiPicker({ open, onClose, onSelect }: EmojiPickerProps) {
  const { t } = useTranslation();
  const [category, setCategory] = useState("smileys");
  const active = EMOJI_CATEGORIES.find((c) => c.id === category) ?? EMOJI_CATEGORIES[0];

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-black/40"
            onClick={onClose}
          />
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 320 }}
            className="fixed inset-x-0 bottom-0 z-50 mx-auto max-w-lg rounded-t-3xl bg-[#1c1428]/95 backdrop-blur-2xl"
            style={{ paddingBottom: "max(0.5rem, env(safe-area-inset-bottom))" }}
          >
            {/* iOS-style handle */}
            <div className="flex justify-center pt-2 pb-1">
              <div className="h-1 w-9 rounded-full bg-accent/25" />
            </div>

            <div className="px-3 pb-2" style={{ borderBottom: `1px solid ${CHAT_BORDER}` }}>
              <p className="text-center text-xs font-medium text-text-muted">{t("common.emoji")}</p>
            </div>

            <div className="grid max-h-[220px] grid-cols-8 gap-0.5 overflow-y-auto px-2 py-2">
              {active.emojis.map((emoji) => (
                <button
                  key={emoji}
                  type="button"
                  onClick={() => onSelect(emoji)}
                  className="flex h-10 w-full items-center justify-center rounded-lg text-2xl transition-colors hover:bg-accent/10 active:bg-accent/15"
                >
                  {emoji}
                </button>
              ))}
            </div>

            {/* Category tabs — iOS style bottom row */}
            <div className="flex items-center justify-around px-2 py-2" style={{ borderTop: `1px solid ${CHAT_BORDER}` }}>
              {EMOJI_CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  aria-label={t(cat.labelKey)}
                  onClick={() => setCategory(cat.id)}
                  className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-xl text-xl transition-colors",
                    category === cat.id ? "bg-accent/25" : "opacity-50 hover:opacity-80"
                  )}
                >
                  {cat.icon}
                </button>
              ))}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export function useEmojiPicker() {
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  return { open, setOpen, inputRef };
}
