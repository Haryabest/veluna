"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavStore } from "@/store/nav-store";
import { useChatsListStore, mapApiChatDetail } from "@/store/chats-list-store";
import { ChatPhotoGenerateModal } from "@/components/chats/ChatPhotoGenerateModal";
import { characterService, chatService, generationService } from "@/services/api";
import { getApiError } from "@/lib/api-client";
import { QUERY_KEYS } from "@/lib/constants";
import { EmojiPicker } from "@/components/widgets/EmojiPicker";
import { AnimeGemIcon } from "@/components/icons/CurrencyIcons";
import { BackButton } from "@/components/shared/BackButton";
import {
  ChatSettingsMenu,
  type ChatMenuAnchor,
} from "@/components/chats/ChatSettingsMenu";
import { MessageSkeleton } from "@/components/shared/Skeleton";
import type { CharacterNarrator } from "@/components/views/NarratorSelectView";
import { ChatThinkingBubble } from "@/components/chats/ChatThinkingBubble";
import {
  MessageContextMenu,
  type MessageMenuAnchor,
} from "@/components/chats/MessageContextMenu";
import { useMessageLongPress } from "@/hooks/use-message-long-press";
import { useToast } from "@/hooks/use-toast";
import { renderMarkdownLite } from "@/lib/markdown-lite";
import { cn } from "@/lib/utils";
import { readMessagesCache, writeMessagesCache } from "@/lib/chat-messages-cache";
import { CHAT_BORDER } from "@/lib/theme";
import type { CharacterScenario } from "@/store/character-store";
import { X } from "lucide-react";

const PHOTO_GRADIENT_BORDER =
  "linear-gradient(135deg, #e9d5ff 0%, #d8b4fe 18%, #c084fc 38%, #a855f7 58%, #9333ea 78%, #7c3aed 100%)";
const PHOTO_GRADIENT_BG =
  "linear-gradient(135deg, #7c3aed 0%, #6d28d9 20%, #5b21b6 40%, #4c1d95 60%, #3b0764 80%, #312e81 100%)";

type ChatMessage = {
  id: string;
  role: string;
  content: string;
  created_at?: string;
  reply_to_id?: string | null;
  reply_preview?: { id: string; role: string; content: string } | null;
};

function mapApiMessage(raw: {
  id: string;
  role: string;
  content: string;
  created_at?: string;
  reply_to_id?: string | null;
  reply_preview?: { id: string; role: string; content: string } | null;
}): ChatMessage {
  return {
    id: String(raw.id),
    role: raw.role,
    content: raw.content,
    created_at: raw.created_at,
    reply_to_id: raw.reply_to_id ?? null,
    reply_preview: raw.reply_preview ?? null,
  };
}

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
  const listChat = useChatsListStore((s) => (chatId ? s.getChat(chatId) : undefined));
  const loadChats = useChatsListStore((s) => s.load);
  const upsertChat = useChatsListStore((s) => s.upsertFromDetail);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [input, setInput] = useState("");
  const [emojiOpen, setEmojiOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState<ChatMenuAnchor | null>(null);
  const [switching, setSwitching] = useState(false);
  const [replyTo, setReplyTo] = useState<ChatMessage | null>(null);
  const [msgMenuOpen, setMsgMenuOpen] = useState(false);
  const [msgMenuAnchor, setMsgMenuAnchor] = useState<MessageMenuAnchor | null>(null);
  const [selectedMessage, setSelectedMessage] = useState<ChatMessage | null>(null);
  const [photoModalOpen, setPhotoModalOpen] = useState(false);
  const [pendingGenerationId, setPendingGenerationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const menuBtnRef = useRef<HTMLButtonElement>(null);
  const prevAiStatusRef = useRef("idle");

  const { data: chatDetail, isLoading: chatLoading } = useQuery({
    queryKey: QUERY_KEYS.chat(chatId ?? ""),
    queryFn: () => chatService.get(chatId!),
    enabled: !!chatId,
    refetchInterval: (query) =>
      query.state.data?.ai_reply_status === "processing" ? 2000 : false,
  });

  const aiReplyStatus = chatDetail?.ai_reply_status ?? "idle";
  const isAiThinking = aiReplyStatus === "processing";

  const chatMeta = listChat ?? (chatDetail ? mapApiChatDetail(chatDetail) : undefined);
  const characterId = chatMeta?.characterId;

  const { data: scenarios = [], isLoading: scenariosLoading } = useQuery<CharacterScenario[]>({
    queryKey: QUERY_KEYS.characterScenarios(characterId ?? ""),
    queryFn: () => characterService.listScenarios(characterId!) as Promise<CharacterScenario[]>,
    enabled: !!characterId && menuOpen,
  });

  const { data: narrators = [], isLoading: narratorsLoading } = useQuery<CharacterNarrator[]>({
    queryKey: QUERY_KEYS.characterNarrators(characterId ?? ""),
    queryFn: () =>
      characterService.listNarrators(characterId!) as Promise<CharacterNarrator[]>,
    enabled: !!characterId && menuOpen,
  });

  const { data: messages, isLoading } = useQuery({
    queryKey: QUERY_KEYS.messages(chatId ?? ""),
    queryFn: async () => {
      const list = await chatService.getMessages(chatId!);
      if (chatId) writeMessagesCache(chatId, list);
      return list;
    },
    enabled: !!chatId,
    staleTime: 2 * 60_000,
    gcTime: 15 * 60_000,
    placeholderData: () => (chatId ? readMessagesCache(chatId) : undefined),
    refetchInterval: isAiThinking ? 2000 : false,
  });

  const { data: pendingGeneration } = useQuery({
    queryKey: [...QUERY_KEYS.generations, "chat", pendingGenerationId] as const,
    queryFn: () => generationService.getById(pendingGenerationId!),
    enabled: !!pendingGenerationId,
    refetchInterval: (query) => {
      const status = query.state.data?.status as string | undefined;
      return status === "pending" || status === "processing" ? 1800 : false;
    },
  });

  useEffect(() => {
    if (!chatId || !pendingGenerationId || !pendingGeneration) return;
    const status = pendingGeneration.status as string;
    if (status !== "completed") {
      if (status === "failed" || status === "moderated") {
        toast("Генерация не удалась", "error");
        setPendingGenerationId(null);
      }
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const artMsg = await chatService.attachArt(chatId, pendingGenerationId);
        if (cancelled) return;
        const mapped = mapApiMessage(artMsg);
        queryClient.setQueryData<ChatMessage[]>(QUERY_KEYS.messages(chatId), (old) => {
          const list = Array.isArray(old) ? old : [];
          if (list.some((m) => m.id === mapped.id)) return list;
          return [...list, mapped];
        });
        void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.messages(chatId) });
      } catch (err) {
        if (!cancelled) toast(getApiError(err).message || "Не удалось добавить арт в чат", "error");
      } finally {
        if (!cancelled) setPendingGenerationId(null);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [chatId, pendingGeneration, pendingGenerationId, queryClient, toast]);

  const sendMutation = useMutation({
    mutationFn: ({ content, replyToId }: { content: string; replyToId?: string }) =>
      chatService.sendMessage(chatId!, content, replyToId),
    onSuccess: (data) => {
      if (!chatId) return;
      const key = QUERY_KEYS.messages(chatId);
      const userMsg = mapApiMessage(data.user_message);
      queryClient.setQueryData<ChatMessage[]>(key, (old) => {
        const list = Array.isArray(old) ? old : [];
        if (list.some((m) => m.id === userMsg.id)) return list;
        return [...list, userMsg];
      });
      queryClient.setQueryData(QUERY_KEYS.chat(chatId), (old: Record<string, unknown> | undefined) => ({
        ...(old ?? {}),
        ai_reply_status: "processing",
        ai_reply_error: null,
      }));
      setReplyTo(null);
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.chat(chatId) });
      useChatsListStore.getState().load();
    },
    onError: (err) => {
      toast(getApiError(err).message || "Не удалось отправить сообщение", "error");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: ({ messageId, scope }: { messageId: string; scope: "self" | "all" }) =>
      chatService.deleteMessage(chatId!, messageId, scope),
    onSuccess: () => {
      if (!chatId) return;
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.messages(chatId) });
    },
    onError: (err) => {
      toast(getApiError(err).message || "Не удалось удалить сообщение", "error");
    },
  });

  useEffect(() => {
    if (prevAiStatusRef.current === "processing" && aiReplyStatus === "failed") {
      toast(chatDetail?.ai_reply_error || "Не удалось получить ответ персонажа", "error");
    }
    prevAiStatusRef.current = aiReplyStatus;
  }, [aiReplyStatus, chatDetail?.ai_reply_error, toast]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isAiThinking, sendMutation.isPending, pendingGenerationId]);

  const openScenarioMenu = useCallback(() => {
    const el = menuBtnRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    setMenuAnchor({ top: rect.bottom, left: rect.left, width: rect.width });
    setMenuOpen(true);
  }, []);

  const handleSwitchScenario = async (scenarioId: string) => {
    if (!chatId || !chatMeta || scenarioId === chatMeta.scenarioId) {
      setMenuOpen(false);
      return;
    }
    setSwitching(true);
    try {
      const chat = await chatService.switchScenario(chatId, scenarioId);
      upsertChat(chat);
      await loadChats();
      setMenuOpen(false);
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.messages(chatId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.chat(chatId) });
    } catch (err) {
      toast(getApiError(err).message || "Не удалось переключить сценарий", "error");
    } finally {
      setSwitching(false);
    }
  };

  const handleSwitchNarrator = async (narratorId: string) => {
    if (!chatId || !chatMeta || narratorId === chatMeta.narratorId) {
      setMenuOpen(false);
      return;
    }
    setSwitching(true);
    try {
      const chat = await chatService.switchNarrator(chatId, narratorId);
      upsertChat(chat);
      await loadChats();
      setMenuOpen(false);
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.messages(chatId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.chat(chatId) });
    } catch (err) {
      toast(getApiError(err).message || "Не удалось переключить рассказчика", "error");
    } finally {
      setSwitching(false);
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
  const narratorName = chatMeta.narratorName;
  const avatarUrl = chatMeta.avatarUrl;
  const displayMessages: ChatMessage[] = Array.isArray(messages) ? messages : [];

  const openMessageMenu = useCallback((msg: ChatMessage, clientX: number, clientY: number) => {
    if (msg.role === "system") return;
    setSelectedMessage(msg);
    setMsgMenuAnchor({ top: clientY, left: clientX });
    setMsgMenuOpen(true);
  }, []);

  const handleCopyMessage = async () => {
    if (!selectedMessage) return;
    try {
      await navigator.clipboard.writeText(selectedMessage.content);
      toast("Скопировано", "success");
    } catch {
      toast("Не удалось скопировать", "error");
    }
    setMsgMenuOpen(false);
  };

  const handleReplyMessage = () => {
    if (!selectedMessage) return;
    setReplyTo(selectedMessage);
    setMsgMenuOpen(false);
    inputRef.current?.focus();
  };

  const handleDeleteMessage = (scope: "self" | "all") => {
    if (!selectedMessage || !chatId) return;
    deleteMutation.mutate({ messageId: selectedMessage.id, scope });
    setMsgMenuOpen(false);
    setSelectedMessage(null);
  };

  const handleSend = () => {
    const text = input.trim();
    if (!text || sendMutation.isPending || isAiThinking || !chatId) return;
    sendMutation.mutate({ content: text, replyToId: replyTo?.id });
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
            {[scenarioTitle, narratorName].filter(Boolean).join(" · ") || "онлайн"}
          </p>
        </div>
        <button
          ref={menuBtnRef}
          type="button"
          aria-label="Настройки чата"
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

      <ChatSettingsMenu
        open={menuOpen}
        anchor={menuAnchor}
        scenarios={scenarios}
        narrators={narrators}
        currentScenarioId={chatMeta.scenarioId}
        currentNarratorId={chatMeta.narratorId}
        loadingScenarios={scenariosLoading}
        loadingNarrators={narratorsLoading}
        switching={switching}
        onClose={() => setMenuOpen(false)}
        onSelectScenario={handleSwitchScenario}
        onSelectNarrator={handleSwitchNarrator}
      />

      <MessageContextMenu
        open={msgMenuOpen}
        anchor={msgMenuAnchor}
        canDelete={selectedMessage?.role !== "system"}
        onClose={() => setMsgMenuOpen(false)}
        onCopy={handleCopyMessage}
        onReply={handleReplyMessage}
        onDeleteSelf={() => handleDeleteMessage("self")}
        onDeleteAll={() => handleDeleteMessage("all")}
      />

      <div
        className="relative z-10 flex-1 space-y-3 overflow-y-auto px-4 py-4"
        style={{
          paddingBottom:
            "calc(11.5rem + 20px + max(0.75rem, env(safe-area-inset-bottom, 0px)))",
        }}
      >
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <MessageSkeleton key={i} />
            ))}
          </div>
        ) : (
          displayMessages.map((msg) => (
            <ChatMessageBubble key={msg.id} msg={msg} onLongPress={openMessageMenu} />
          ))
        )}
        {pendingGenerationId ? <ChatArtGeneratingBubble /> : null}
        {isAiThinking && <ChatThinkingBubble />}
        <div ref={messagesEndRef} />
      </div>

      <div
        className="fixed inset-x-0 z-30 mx-auto flex max-w-lg flex-col gap-3 px-3"
        style={{
          bottom: "calc(20px + max(0.75rem, env(safe-area-inset-bottom, 0px)))",
        }}
      >
        {replyTo ? (
          <div
            className="flex items-center gap-2 rounded-2xl bg-bg-elevated/90 px-3 py-2"
            style={{ border: `1px solid ${CHAT_BORDER}` }}
          >
            <div className="min-w-0 flex-1 border-l-2 border-accent-light pl-2">
              <p className="text-[11px] font-semibold text-accent-light">Ответ</p>
              <p className="truncate text-xs text-text-muted">{replyTo.content}</p>
            </div>
            <button
              type="button"
              aria-label="Отменить ответ"
              onClick={() => setReplyTo(null)}
              className="shrink-0 rounded-full p-1 text-text-muted hover:bg-bg-elevated"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : null}

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
            disabled={!hasText || sendMutation.isPending || isAiThinking}
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
            onClick={() => setPhotoModalOpen(true)}
            disabled={!!pendingGenerationId || isAiThinking}
            className="flex w-full items-center gap-3 rounded-[14px] px-4 py-3.5 text-left transition-transform active:scale-[0.98] disabled:opacity-60"
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

      {characterId ? (
        <ChatPhotoGenerateModal
          open={photoModalOpen}
          characterId={characterId}
          characterName={characterName}
          onClose={() => setPhotoModalOpen(false)}
          onStarted={(id) => setPendingGenerationId(id)}
        />
      ) : null}
    </div>
  );
}

function ChatArtGeneratingBubble() {
  return (
    <div className="flex items-start">
      <div
        className="rounded-[18px] rounded-bl-[4px] px-3.5 py-2.5 text-sm text-text-secondary backdrop-blur-md"
        style={{ border: `1px solid ${CHAT_BORDER}`, background: "rgba(26, 18, 40, 0.72)" }}
      >
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 animate-pulse rounded-full bg-pink-400" />
          Создаю арт…
        </span>
      </div>
    </div>
  );
}

function ChatMessageBubble({
  msg,
  onLongPress,
}: {
  msg: ChatMessage;
  onLongPress: (msg: ChatMessage, x: number, y: number) => void;
}) {
  const longPress = useMessageLongPress(
    (x, y) => onLongPress(msg, x, y),
    { disabled: msg.role === "system" }
  );

  if (msg.role === "system") {
    return (
      <div className="flex justify-center px-2 py-1">
        <p className="max-w-[90%] text-center text-xs leading-relaxed text-text-muted">
          {msg.content}
        </p>
      </div>
    );
  }

  return (
    <div
      className={cn("flex flex-col select-none", msg.role === "user" ? "items-end" : "items-start")}
      {...longPress.bind()}
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
        {msg.reply_preview ? (
          <div
            className="mb-2 rounded-lg border-l-2 border-white/40 bg-black/15 px-2 py-1 text-xs opacity-90"
            style={{ borderColor: msg.role === "user" ? "rgba(255,255,255,0.5)" : undefined }}
          >
            <p className="line-clamp-2">{msg.reply_preview.content}</p>
          </div>
        ) : null}
        <span className="whitespace-pre-wrap">{renderMarkdownLite(msg.content)}</span>
      </div>
      <span className="mt-1 px-1 text-[11px] text-text-muted">{formatTime(msg.created_at)}</span>
    </div>
  );
}
