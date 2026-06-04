import { create } from "zustand";
import { chatListService, chatService } from "@/services/api";

export type ChatListItem = {
  id: string;
  characterId: string;
  characterName: string;
  avatarUrl: string;
  preview: string;
  time: string;
  unread?: number;
  isSystem?: boolean;
  isPinned: boolean;
  displayName: string;
};

function formatChatTime(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const sameDay =
    d.getDate() === now.getDate() &&
    d.getMonth() === now.getMonth() &&
    d.getFullYear() === now.getFullYear();
  if (sameDay) {
    return d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  }
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000);
  if (diffDays === 1) return "Вчера";
  if (diffDays < 7) {
    return d.toLocaleDateString("ru-RU", { weekday: "short" });
  }
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
}

function mapApiChat(raw: {
  id: string;
  character_id: string;
  character_name: string;
  character_avatar_url?: string | null;
  display_title: string;
  is_pinned?: boolean;
  is_system?: boolean;
  last_message_preview?: string | null;
  last_message_at?: string | null;
  unread?: number;
}): ChatListItem {
  return {
    id: raw.id,
    characterId: raw.character_id,
    characterName: raw.character_name,
    avatarUrl: raw.character_avatar_url || "",
    preview: raw.last_message_preview || "Начни диалог…",
    time: formatChatTime(raw.last_message_at),
    unread: raw.unread ?? 0,
    isSystem: raw.is_system ?? false,
    isPinned: raw.is_pinned ?? false,
    displayName: raw.display_title || raw.character_name,
  };
}

function sortChats(chats: ChatListItem[]): ChatListItem[] {
  return chats
    .map((c, index) => ({ c, index }))
    .sort((a, b) => {
      if (a.c.isPinned !== b.c.isPinned) return a.c.isPinned ? -1 : 1;
      return a.index - b.index;
    })
    .map(({ c }) => c);
}

interface ChatsListState {
  chats: ChatListItem[];
  initialized: boolean;
  loading: boolean;
  load: () => Promise<void>;
  getChat: (id: string) => ChatListItem | undefined;
  pinChat: (id: string) => Promise<void>;
  renameChat: (id: string, title: string) => Promise<void>;
  removeChat: (id: string) => Promise<void>;
}

export const useChatsListStore = create<ChatsListState>((set, get) => ({
  chats: [],
  initialized: false,
  loading: false,

  load: async () => {
    set({ loading: true });
    try {
      const data = await chatService.list(1);
      const items = Array.isArray(data.items) ? data.items.map(mapApiChat) : [];
      set({ chats: sortChats(items), initialized: true, loading: false });
    } catch {
      set({ chats: [], initialized: true, loading: false });
    }
  },

  getChat: (id) => get().chats.find((c) => c.id === id),

  pinChat: async (id) => {
    const chat = get().chats.find((c) => c.id === id);
    if (!chat) return;
    const pinned = !chat.isPinned;
    await chatListService.pin(id, pinned);
    set({
      chats: sortChats(
        get().chats.map((c) => (c.id === id ? { ...c, isPinned: pinned } : c))
      ),
    });
  },

  renameChat: async (id, title) => {
    const trimmed = title.trim();
    if (!trimmed) return;
    await chatListService.rename(id, trimmed);
    set({
      chats: get().chats.map((c) =>
        c.id === id ? { ...c, displayName: trimmed } : c
      ),
    });
  },

  removeChat: async (id) => {
    await chatListService.remove(id);
    set({ chats: get().chats.filter((c) => c.id !== id) });
  },
}));
