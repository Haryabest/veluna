"use client";

import { useState, useRef, useEffect } from "react";
import { useNavStore } from "@/store/nav-store";
import { useChatsListStore } from "@/store/chats-list-store";
import { getMockChat, getMockMessages, type MockMessage } from "@/lib/mock-data";
import { EmojiPicker } from "@/components/widgets/EmojiPicker";
import { AnimeGemIcon } from "@/components/icons/CurrencyIcons";
import { BackButton } from "@/components/shared/BackButton";
import { cn } from "@/lib/utils";

const PHOTO_GRADIENT_BORDER =
  "linear-gradient(135deg, #e9d5ff 0%, #d8b4fe 18%, #c084fc 38%, #a855f7 58%, #9333ea 78%, #7c3aed 100%)";
const PHOTO_GRADIENT_BG =
  "linear-gradient(135deg, #7c3aed 0%, #6d28d9 20%, #5b21b6 40%, #4c1d95 60%, #3b0764 80%, #312e81 100%)";
import { CHAT_BORDER } from "@/lib/theme";

function formatTime() {
  return new Date().toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
}

function EmojiSmileIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.5" />
      <path d="M8.5 14.5c.9 1.2 2.1 1.8 3.5 1.8s2.6-.6 3.5-1.8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="9" cy="10" r="1" fill="currentColor" />
      <circle cx="15" cy="10" r="1" fill="currentColor" />
    </svg>
  );
}

function SendIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M2.01 21 23 12 2.01 3 2 10l15 2-15 2z" />
    </svg>
  );
}

export function ChatDialogView() {
  const chatId = useNavStore((s) => s.chatId);
  const goBack = useNavStore((s) => s.goBack);
  const listChat = useChatsListStore((s) => (chatId ? s.getChat(chatId) : undefined));

  const chat = chatId ? getMockChat(chatId) : null;
  const characterName = listChat?.displayName ?? chat?.characterName ?? "";
  const [messages, setMessages] = useState<MockMessage[]>(() =>
    chatId ? getMockMessages(chatId) : []
  );
  const [input, setInput] = useState("");
  const [emojiOpen, setEmojiOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (chatId) setMessages(getMockMessages(chatId));
  }, [chatId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!chat || !chatId) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-text-muted">Чат не найден</p>
      </div>
    );
  }

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;
    const userMsg: MockMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      content: text,
      time: formatTime(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setEmojiOpen(false);

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          content: "Мм... интересно! Расскажи ещё 💜",
          time: formatTime(),
        },
      ]);
    }, 1200);
  };

  const insertEmoji = (emoji: string) => {
    setInput((prev) => prev + emoji);
    inputRef.current?.focus();
  };

  const hasText = input.trim().length > 0;

  return (
    <div className="relative mx-auto flex h-[100dvh] max-w-lg flex-col overflow-hidden bg-transparent">
      <header className="relative z-10 flex shrink-0 items-center gap-2 px-3 py-2.5 pt-[max(0.5rem,env(safe-area-inset-top))]">
        <BackButton onClick={goBack} />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={chat.avatarUrl} alt="" className="h-9 w-9 shrink-0 rounded-full object-cover" />
        <div className="min-w-0 flex-1">
          <p className="truncate text-[15px] font-semibold">{characterName}</p>
          <p className="text-xs text-emerald-400">онлайн</p>
        </div>
        <button
          type="button"
          aria-label="Меню"
          className="flex h-9 w-9 shrink-0 items-center justify-center text-text-muted"
        >
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="5" cy="12" r="1.5" />
            <circle cx="12" cy="12" r="1.5" />
            <circle cx="19" cy="12" r="1.5" />
          </svg>
        </button>
      </header>

      <div
        className="relative z-10 flex-1 space-y-3 overflow-y-auto px-4 py-4"
        style={{
          paddingBottom:
            "calc(11.5rem + 20px + max(0.75rem, env(safe-area-inset-bottom, 0px)))",
        }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn("flex flex-col", msg.role === "user" ? "items-end" : "items-start")}
          >
            <div
              className={cn(
                "max-w-[82%] px-3.5 py-2.5 text-[15px] leading-snug",
                msg.role === "user"
                  ? "rounded-[18px] rounded-br-[4px] text-text-primary"
                  : "rounded-[18px] rounded-bl-[4px] text-text-primary backdrop-blur-md"
              )}
              style={
                msg.role === "user"
                  ? {
                      background: "linear-gradient(135deg, #b45cf0 0%, #7c3aed 50%, #6d28d9 100%)",
                      border: "none",
                    }
                  : {
                      border: `1px solid ${CHAT_BORDER}`,
                      background: "rgba(26, 18, 40, 0.72)",
                    }
              }
            >
              {msg.content}
            </div>
            <span className="mt-1 px-1 text-[11px] text-text-muted">{msg.time}</span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div
        className="fixed inset-x-0 z-30 mx-auto flex max-w-lg flex-col gap-3 px-3"
        style={{
          bottom: "calc(20px + max(0.75rem, env(safe-area-inset-bottom, 0px)))",
        }}
      >
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setEmojiOpen((v) => !v)}
            aria-label="Эмодзи"
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-colors",
              emojiOpen ? "bg-accent/20 text-accent-light" : "text-text-muted hover:bg-bg-elevated"
            )}
          >
            <EmojiSmileIcon className="h-6 w-6" />
          </button>

          <div
            className="flex min-h-[44px] flex-1 items-center rounded-full bg-bg-elevated px-4"
            style={{ border: `1px solid ${CHAT_BORDER}` }}
          >
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Сообщение"
              className="min-w-0 flex-1 bg-transparent text-[16px] text-text-primary outline-none ring-0 placeholder:text-text-muted focus:outline-none focus:ring-0"
            />
          </div>

          <button
            type="button"
            onClick={handleSend}
            disabled={!hasText}
            aria-label="Отправить"
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-all active:scale-90",
              hasText ? "bg-accent text-text-primary shadow-[0_0_14px_rgba(160,32,240,0.45)]" : "bg-bg-elevated text-text-muted"
            )}
            style={!hasText ? { border: `1px solid ${CHAT_BORDER}` } : undefined}
          >
            <SendIcon className="h-5 w-5" />
          </button>
        </div>

        <div
          className="rounded-2xl p-[1.5px] shadow-[0_0_24px_rgba(168,85,247,0.38)]"
          style={{ background: PHOTO_GRADIENT_BORDER }}
        >
          <button
            type="button"
            className="flex w-full items-center gap-3 rounded-[14px] px-4 py-3.5 text-left transition-transform active:scale-[0.98]"
            style={{
              background: PHOTO_GRADIENT_BG,
              boxShadow: "inset 0 1px 0 rgba(255,255,255,0.12)",
            }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={chat.avatarUrl}
              alt=""
              className="h-11 w-11 shrink-0 rounded-xl object-cover"
              style={{ border: `1px solid ${CHAT_BORDER}` }}
            />
            <div className="min-w-0 flex-1">
              <p className="text-[14px] font-bold uppercase tracking-wide text-white">
                Сгенерировать фото
              </p>
              <p className="mt-0.5 flex items-center gap-1.5 text-sm font-medium text-white/90">
                5 <AnimeGemIcon className="h-4 w-4" />
              </p>
            </div>
            <svg
              className="h-5 w-5 shrink-0 text-text-muted"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M9 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>

      <EmojiPicker open={emojiOpen} onClose={() => setEmojiOpen(false)} onSelect={insertEmoji} />
    </div>
  );
}
