import { create } from "zustand";
import { MOCK_CHATS, type MockChat } from "@/lib/mock-data";
import { chatListService } from "@/services/api";

export type ChatListItem = MockChat & {
  isPinned: boolean;
  displayName: string;
};

function sortChats(chats: ChatListItem[]): ChatListItem[] {
  return chats
    .map((c, index) => ({ c, index }))
    .sort((a, b) => {
      if (a.c.isPinned !== b.c.isPinned) return a.c.isPinned ? -1 : 1;
      return a.index - b.index;
    })
    .map(({ c }) => c);
}

function toListItem(chat: MockChat): ChatListItem {
  return { ...chat, isPinned: false, displayName: chat.characterName };
}

interface ChatsListState {
  chats: ChatListItem[];
  initialized: boolean;
  init: () => void;
  getChat: (id: string) => ChatListItem | undefined;
  pinChat: (id: string) => Promise<void>;
  renameChat: (id: string, title: string) => Promise<void>;
  removeChat: (id: string) => Promise<void>;
}

export const useChatsListStore = create<ChatsListState>((set, get) => ({
  chats: [],
  initialized: false,

  init: () => {
    if (get().initialized) return;
    set({ chats: MOCK_CHATS.map(toListItem), initialized: true });
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
        c.id === id ? { ...c, displayName: trimmed, characterName: trimmed } : c
      ),
    });
  },

  removeChat: async (id) => {
    await chatListService.remove(id);
    set({ chats: get().chats.filter((c) => c.id !== id) });
  },
}));
