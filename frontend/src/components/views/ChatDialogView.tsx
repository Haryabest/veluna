"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavStore } from "@/store/nav-store";
import { useChatsListStore, mapApiChatDetail } from "@/store/chats-list-store";
import { characterService, chatService } from "@/services/api";
import { QUERY_KEYS } from "@/lib/constants";
import { EmojiPicker } from "@/components/widgets/EmojiPicker";
import { AnimeGemIcon } from "@/components/icons/CurrencyIcons";
import { BackButton } from "@/components/shared/BackButton";
import {
  ChatScenarioMenu,
  type ChatMenuAnchor,
} from "@/components/chats/ChatScenarioMenu";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import { CHAT_BORDER } from "@/lib/theme";
import type { CharacterScenario } from "@/store/character-store";

const PHOTO_GRADIENT_BORDER =
  "linear-gradient(135deg, #e9d5ff 0%, #d8b4fe 18%, #c084fc 38%, #a855f7 58%, #9333ea 78%, #7c3aed 100%)";
const PHOTO_GRADIENT_BG =
  "linear-gradient(135deg, #7c3aed 0%, #6d28d9 20%, #5b21b6 40%, #4c1d95 60%, #3b0764 80%, #312e81 100%)";

type ChatMessage = {
  id: string;
  role: string;
  content: string;
  created_at?: string;
};

function formatTime(iso?: string) {
  if (!iso) {
    return new Date().toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  }
  return new Date(iso).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
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

function ChatAvatar({
  src,
  name,
  className,
}: {
  src?: string | null;
  name: string;
  className: string;
}) {
  if (src) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={src} alt="" className={className} />
    );
  }

  return (
    <div
      className={cn(
        "flex shrink-0 items-center justify-center bg-bg-elevated text-sm font-bold text-text-muted",
        className
      )}
    >
      {name.trim().charAt(0) || "?"}
    </div>
  );
}

export function ChatDialogView() {
  const chatId = useNavStore((s) => s.chatId);
  const goBack = useNavStore((s) => s.goBack);
  const openChat = useNavStore((s) => s.openChat);
  const listChat = useChatsListStore((s) => (chatId ? s.getChat(chatId) : undefined));
  const loadChats = useChatsListStore((s) => s.load);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [input, setInput] = useState("");
  const [emojiOpen, setEmojiOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState<ChatMenuAnchor | null>(null);
  const [switchingScenario, setSwitchingScenario] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const menuBtnRef = useRef<HTMLButtonElement>(null);

  const { data: chatDetail, isLoading: chatLoading } = useQuery({
    queryKey: QUERY_KEYS.chat(chatId ?? ""),
    queryFn: () => chatService.get(chatId!),
    enabled: !!chatId && !listChat,
  });

  const chatMeta = listChat ?? (chatDetail ? mapApiChatDetail(chatDetail) : undefined);
  const characterId = chatMeta?.characterId;

  const { data: scenarios = [], isLoading: scenariosLoading } = useQuery<CharacterScenario[]>({
    queryKey: QUERY_KEYS.characterScenarios(characterId ?? ""),
    queryFn: () => characterService.listScenarios(characterId!) as Promise<CharacterScenario[]>,
    enabled: !!characterId && menuOpen,
  });

  const { data: messages, isLoading } = useQuery({
    queryKey: QUERY_KEYS.messages(chatId ?? ""),
    queryFn: () => chatService.getMessages(chatId!),
    enabled: !!chatId,
  });

  const sendMutation = useMutation({
    mutationFn: (content: string) => chatService.sendMessage(chatId!, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.messages(chatId ?? "") });
      useChatsListStore.getState().load();
    },
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sendMutation.isPending]);

  const openScenarioMenu = useCallback(() => {
    const el = menuBtnRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    setMenuAnchor({ top: rect.bottom, left: rect.left, width: rect.width });
    setMenuOpen(true);
  }, []);

  const handleSwitchScenario = async (scenarioId: string) => {
    if (!characterId || !chatMeta || scenarioId === chatMeta.scenarioId) {
      setMenuOpen(false);
      return;
    }
    setSwitchingScenario(true);
    try {
      const chat = await chatService.create(characterId, scenarioId);
      await loadChats();
      setMenuOpen(false);
      queryClient.removeQueries({ queryKey: QUERY_KEYS.messages(chatId ?? "") });
      openChat(chat.id);
    } catch {
      toast("Не удалось переключить сценарий", "error");
    } finally {
      setSwitchingScenario(false);
    }
  };

  if (!chatId || (!chatMeta && chatLoading)) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-text-muted">Загрузка чата…</p>
      </div>
    );
  }

  if (!chatMeta) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-text-muted">Чат не найден</p>
      </div>
    );
  }

  const characterName = chatMeta.characterName;
  const scenarioTitle = chatMeta.scenarioTitle;
  const avatarUrl = chatMeta.avatarUrl;
  const messageList: ChatMessage[] = Array.isArray(messages) ? messages : [];

  const handleSend = () => {
    const text = input.trim();
    if (!text || sendMutation.isPending) return;
    sendMutation.mutate(text);
    setInput("");
    setEmojiOpen(false);
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
        <ChatAvatar
          src={avatarUrl}
          name={characterName}
          className="h-9 w-9 rounded-full object-cover"
        />
        <div className="min-w-0 flex-1">
          <p className="truncate text-[15px] font-semibold">{characterName}</p>
          <p className="truncate text-xs text-accent-light/90">
            {scenarioTitle ?? "онлайн"}
          </p>
        </div>
        <button
          ref={menuBtnRef}
          type="button"
          aria-label="Сменить сценарий"
          aria-expanded={menuOpen}
          onClick={openScenarioMenu}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-text-muted transition-colors hover:bg-bg-elevated/80 hover:text-text-primary"
        >
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="5" cy="12" r="1.5" />
            <circle cx="12" cy="12" r="1.5" />
            <circle cx="19" cy="12" r="1.5" />
          </svg>
        </button>
      </header>

      <ChatScenarioMenu
        open={menuOpen}
        anchor={menuAnchor}
        scenarios={scenarios}
        currentScenarioId={chatMeta.scenarioId}
        loading={scenariosLoading}
        switching={switchingScenario}
        onClose={() => setMenuOpen(false)}
        onSelect={handleSwitchScenario}
      />

      <div
        className="relative z-10 flex-1 space-y-3 overflow-y-auto px-4 py-4"
        style={{
          paddingBottom:
            "calc(11.5rem + 20px + max(0.75rem, env(safe-area-inset-bottom, 0px)))",
        }}
      >
        {isLoading ? (
          <p className="text-center text-sm text-text-muted">Загрузка сообщений…</p>
        ) : (
          messageList.map((msg) => (
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
              <span className="mt-1 px-1 text-[11px] text-text-muted">{formatTime(msg.created_at)}</span>
            </div>
          ))
        )}
        {sendMutation.isPending && (
          <p className="text-xs text-text-muted">печатает…</p>
        )}
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
            disabled={!hasText || sendMutation.isPending}
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
            <ChatAvatar
              src={avatarUrl}
              name={characterName}
              className="h-11 w-11 shrink-0 rounded-xl object-cover"
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
