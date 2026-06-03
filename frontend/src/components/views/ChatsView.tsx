"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CHAT_BORDER } from "@/lib/theme";
import { useNavStore } from "@/store/nav-store";
import { useChatsListStore } from "@/store/chats-list-store";
import { useLongPress } from "@/hooks/use-long-press";
import { useModal } from "@/hooks/use-modal";
import { useToast } from "@/hooks/use-toast";
import {
  ChatContextMenu,
  type ChatMenuAnchor,
} from "@/components/chats/ChatContextMenu";
import { cn } from "@/lib/utils";
import type { ChatListItem } from "@/store/chats-list-store";

export function ChatsView() {
  const openChat = useNavStore((s) => s.openChat);
  const { toast } = useToast();
  const { openModal, closeModal } = useModal();
  const init = useChatsListStore((s) => s.init);
  const chats = useChatsListStore((s) => s.chats);
  const pinChat = useChatsListStore((s) => s.pinChat);
  const renameChat = useChatsListStore((s) => s.renameChat);
  const removeChat = useChatsListStore((s) => s.removeChat);

  const [menuChatId, setMenuChatId] = useState<string | null>(null);
  const [menuAnchor, setMenuAnchor] = useState<ChatMenuAnchor | null>(null);

  useEffect(() => {
    init();
  }, [init]);

  const menuChat = chats.find((c) => c.id === menuChatId);

  const closeMenu = useCallback(() => {
    setMenuChatId(null);
    setMenuAnchor(null);
  }, []);

  const openMenu = useCallback((chatId: string, el: HTMLElement) => {
    const rect = el.getBoundingClientRect();
    setMenuChatId(chatId);
    setMenuAnchor({ top: rect.bottom, left: rect.left, width: rect.width });
  }, []);

  const handlePin = async () => {
    if (!menuChatId || !menuChat) return;
    const wasPinned = menuChat.isPinned;
    closeMenu();
    try {
      await pinChat(menuChatId);
      toast(wasPinned ? "Чат откреплён" : "Чат закреплён", "success");
    } catch {
      toast("Не удалось изменить закрепление", "error");
    }
  };

  const handleRename = () => {
    if (!menuChat || menuChat.isSystem) return;
    const chatId = menuChat.id;
    const currentName = menuChat.displayName;
    closeMenu();

    openModal({
      type: "custom",
      title: "Переименовать чат",
      content: (
        <RenameChatForm
          defaultValue={currentName}
          onSubmit={async (title) => {
            try {
              await renameChat(chatId, title);
              closeModal();
              toast("Чат переименован", "success");
            } catch {
              toast("Не удалось переименовать", "error");
            }
          }}
        />
      ),
    });
  };

  const handleDelete = () => {
    if (!menuChat || menuChat.isSystem) return;
    const chatId = menuChat.id;
    closeMenu();

    openModal({
      type: "confirm",
      title: "Удалить чат?",
      content: (
        <p>
          Диалог с <span className="font-semibold text-text-primary">{menuChat.displayName}</span>{" "}
          будет удалён. Это действие нельзя отменить.
        </p>
      ),
      onConfirm: async () => {
        try {
          await removeChat(chatId);
          toast("Чат удалён", "success");
        } catch {
          toast("Не удалось удалить чат", "error");
        }
      },
    });
  };

  return (
    <div className="mx-auto max-w-lg px-4 pt-5">
      <header className="mb-4">
        <h1 className="text-2xl font-bold">Чаты</h1>
      </header>

      {chats.length === 0 ? (
        <p className="py-12 text-center text-sm text-text-muted">Нет чатов</p>
      ) : (
        <div
          className="overflow-hidden rounded-2xl bg-bg-elevated/40 backdrop-blur-md"
          style={{ border: `1px solid ${CHAT_BORDER}` }}
        >
          {chats.map((chat, i) => (
            <ChatRow
              key={chat.id}
              chat={chat}
              showBorder={i < chats.length - 1}
              onOpen={() => openChat(chat.id)}
              onLongPress={(el) => openMenu(chat.id, el)}
            />
          ))}
        </div>
      )}

      <ChatContextMenu
        open={Boolean(menuChatId && menuAnchor)}
        anchor={menuAnchor}
        isPinned={menuChat?.isPinned ?? false}
        isSystem={menuChat?.isSystem}
        onClose={closeMenu}
        onPin={handlePin}
        onRename={handleRename}
        onDelete={handleDelete}
      />
    </div>
  );
}

function ChatRow({
  chat,
  showBorder,
  onOpen,
  onLongPress,
}: {
  chat: ChatListItem;
  showBorder: boolean;
  onOpen: () => void;
  onLongPress: (el: HTMLElement) => void;
}) {
  const {
    isHolding,
    isTriggered,
    tapPulse,
    holdDurationMs,
    onTouchStart,
    onTouchEnd,
    onTouchCancel,
    onMouseDown,
    onMouseUp,
    onMouseLeave,
    suppressClick,
  } = useLongPress(
    () => {
      const el = document.getElementById(`chat-row-${chat.id}`);
      if (el) onLongPress(el);
    },
    onOpen
  );

  return (
    <motion.button
      id={`chat-row-${chat.id}`}
      type="button"
      onTouchStart={onTouchStart}
      onTouchEnd={onTouchEnd}
      onTouchCancel={onTouchCancel}
      onMouseDown={onMouseDown}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseLeave}
      onClickCapture={suppressClick}
      initial={{ opacity: 0, y: 8 }}
      animate={{
        opacity: 1,
        y: 0,
        scale: isTriggered ? 0.96 : isHolding ? 0.975 : tapPulse ? 0.985 : 1,
        backgroundColor: isHolding
          ? "rgba(160, 32, 240, 0.12)"
          : isTriggered
            ? "rgba(160, 32, 240, 0.18)"
            : "rgba(0, 0, 0, 0)",
      }}
      transition={{
        scale: { type: "spring", stiffness: 520, damping: 28 },
        backgroundColor: { duration: isHolding ? 0.15 : 0.25 },
      }}
      className={cn(
        "relative flex w-full items-center gap-3 overflow-hidden px-4 py-3.5 text-left",
        !isHolding && !isTriggered && "hover:bg-bg-elevated/60"
      )}
      style={showBorder ? { borderBottom: `1px solid ${CHAT_BORDER}` } : undefined}
    >
      {isHolding && (
        <motion.span
          className="pointer-events-none absolute inset-y-0 left-0 bg-accent/35"
          initial={{ width: "0%" }}
          animate={{ width: "100%" }}
          transition={{ duration: holdDurationMs / 1000, ease: "linear" }}
          aria-hidden
        />
      )}
      {isTriggered && (
        <motion.span
          className="pointer-events-none absolute inset-0 bg-accent/20"
          initial={{ opacity: 0.6 }}
          animate={{ opacity: 0 }}
          transition={{ duration: 0.35 }}
          aria-hidden
        />
      )}
      <div className="relative z-[1] shrink-0">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={chat.avatarUrl}
          alt={chat.displayName}
          className="h-12 w-12 rounded-full object-cover"
        />
        {chat.isSystem && (
          <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-accent" />
        )}
        {chat.isPinned && (
          <span
            className="absolute -left-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-accent text-[9px]"
            aria-label="Закреплён"
          >
            📌
          </span>
        )}
      </div>

      <div className="relative z-[1] min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-2">
          <span className="truncate font-semibold">{chat.displayName}</span>
          <span className="shrink-0 text-xs text-text-muted">{chat.time}</span>
        </div>
        <p className="mt-0.5 truncate text-sm text-text-muted">{chat.preview}</p>
      </div>

      {chat.unread ? (
        <span className="relative z-[1] flex h-5 min-w-5 shrink-0 items-center justify-center rounded-full bg-accent px-1.5 text-[11px] font-bold text-text-primary">
          {chat.unread}
        </span>
      ) : null}
    </motion.button>
  );
}

function RenameChatForm({
  defaultValue,
  onSubmit,
}: {
  defaultValue: string;
  onSubmit: (title: string) => void | Promise<void>;
}) {
  const [value, setValue] = useState(defaultValue);
  const [loading, setLoading] = useState(false);

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (!value.trim() || loading) return;
        setLoading(true);
        await onSubmit(value);
        setLoading(false);
      }}
      className="space-y-3"
    >
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        maxLength={64}
        autoFocus
        className="w-full rounded-xl border border-accent/20 bg-bg-elevated px-3 py-2.5 text-sm text-text-primary outline-none focus:border-accent/50"
        style={{ borderColor: "rgba(90, 50, 130, 0.45)" }}
        placeholder="Название чата"
      />
      <button
        type="submit"
        disabled={!value.trim() || loading}
        className="w-full rounded-xl bg-accent py-2.5 text-sm font-semibold text-text-primary disabled:opacity-50"
      >
        {loading ? "Сохранение…" : "Сохранить"}
      </button>
    </form>
  );
}
