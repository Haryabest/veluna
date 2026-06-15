"use client";

import { motion } from "framer-motion";
import { CHAT_BORDER } from "@/lib/theme";
import { useTranslation } from "@/hooks/use-translation";

export function ChatThinkingBubble() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-start">
      <div
        className="flex max-w-[82%] items-center gap-2 rounded-[18px] rounded-bl-[4px] px-3.5 py-2.5 text-[15px] text-text-primary backdrop-blur-md"
        style={{
          border: `1px solid ${CHAT_BORDER}`,
          background: "rgba(26, 18, 40, 0.72)",
        }}
      >
        <span className="text-text-muted">{t("chat.thinking")}</span>
        <span className="flex items-center gap-1" aria-hidden>
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="h-1.5 w-1.5 rounded-full bg-accent-light"
              animate={{ opacity: [0.35, 1, 0.35], y: [0, -3, 0] }}
              transition={{
                duration: 0.9,
                repeat: Infinity,
                delay: i * 0.18,
                ease: "easeInOut",
              }}
            />
          ))}
        </span>
      </div>
    </div>
  );
}
