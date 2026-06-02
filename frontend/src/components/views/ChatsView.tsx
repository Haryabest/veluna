"use client";

import { motion } from "framer-motion";
import { MOCK_CHATS } from "@/lib/mock-data";
import { CHAT_BORDER } from "@/lib/theme";
import { useNavStore } from "@/store/nav-store";
import { cn } from "@/lib/utils";

export function ChatsView() {
  const openChat = useNavStore((s) => s.openChat);

  return (
    <div className="mx-auto max-w-lg px-4 pt-5">
      <header className="mb-4">
        <h1 className="text-2xl font-bold">Чаты</h1>
      </header>

      <div
        className="overflow-hidden rounded-2xl bg-bg-elevated/40 backdrop-blur-md"
        style={{ border: `1px solid ${CHAT_BORDER}` }}
      >
        {MOCK_CHATS.map((chat, i) => (
          <motion.button
            key={chat.id}
            type="button"
            onClick={() => openChat(chat.id)}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className={cn(
              "flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-bg-elevated/60"
            )}
            style={
              i < MOCK_CHATS.length - 1 ? { borderBottom: `1px solid ${CHAT_BORDER}` } : undefined
            }
          >
            <div className="relative shrink-0">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={chat.avatarUrl}
                alt={chat.characterName}
                className="h-12 w-12 rounded-full object-cover"
              />
              {chat.isSystem && (
                <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-accent" />
              )}
            </div>

            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-2">
                <span className="truncate font-semibold">{chat.characterName}</span>
                <span className="shrink-0 text-xs text-text-muted">{chat.time}</span>
              </div>
              <p className="mt-0.5 truncate text-sm text-text-muted">{chat.preview}</p>
            </div>

            {chat.unread ? (
              <span className="flex h-5 min-w-5 shrink-0 items-center justify-center rounded-full bg-accent px-1.5 text-[11px] font-bold text-text-primary">
                {chat.unread}
              </span>
            ) : null}
          </motion.button>
        ))}
      </div>
    </div>
  );
}
