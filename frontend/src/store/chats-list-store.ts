import { create } from "zustand";
import { chatListService, chatService } from "@/services/api";
import { normalizeLocale, localeTag, t, type AppLocale } from "@/lib/i18n/translations";
import { useSettingsStore } from "@/store/settings-store";

const CHATS_CACHE_KEY = "veluna_chats_cache_v2";
const CHATS_CACHE_TTL_MS = 30 * 60 * 1000;

type ChatsCachePayload = {
  savedAt: number;
  chats: ChatListItem[];
};

function readChatsCache(): ChatListItem[] | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(CHATS_CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as ChatsCachePayload;
    if (Date.now() - parsed.savedAt > CHATS_CACHE_TTL_MS) return null;
    return parsed.chats;
  } catch {
    return null;
  }
}

function writeChatsCache(chats: ChatListItem[]) {
  if (typeof window === "undefined") return;
  try {
    const payload: ChatsCachePayload = { savedAt: Date.now(), chats };
    localStorage.setItem(CHATS_CACHE_KEY, JSON.stringify(payload));
  } catch {
    /* ignore quota */
  }
}

export type ChatListItem = {
  id: string;
  characterId: string;
  characterName: string;
  scenarioId: string | null;
  scenarioTitle: string | null;
  narratorId: string | null;
  narratorName: string | null;
  avatarUrl: string;
  preview: string;
  time: string;
  unread?: number;
  isSystem?: boolean;
  isPinned: boolean;
  displayName: string;
};

function getLocale(): AppLocale {
  if (typeof window === "undefined") return "ru";
  return normalizeLocale(useSettingsStore.getState().language);
}

function formatChatTime(iso: string | null | undefined, locale: AppLocale = getLocale()): string {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const tag = localeTag(locale);
  const sameDay =
    d.getDate() === now.getDate() &&
    d.getMonth() === now.getMonth() &&
    d.getFullYear() === now.getFullYear();
  if (sameDay) {
    return d.toLocaleTimeString(tag, { hour: "2-digit", minute: "2-digit" });
  }
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000);
  if (diffDays === 1) return t(locale, "common.yesterday");
  if (diffDays < 7) {
    return d.toLocaleDateString(tag, { weekday: "short" });
  }
  return d.toLocaleDateString(tag, { day: "numeric", month: "short" });
}

function formatChatPreview(raw: string | null | undefined, locale: AppLocale = getLocale()): string {
  const text = (raw ?? "").trim();
  if (!text) return t(locale, "common.startDialog");
  if (/^!\[[^\]]*\]\([^)]+\)\s*$/.test(text)) return t(locale, "common.photo");
  return text;
}

function mapApiChat(raw: {
  id: string;
  character_id: string;
  character_name: string;
  scenario_id?: string | null;
  scenario_title?: string | null;
  narrator_id?: string | null;
  narrator_name?: string | null;
  character_avatar_url?: string | null;
  display_title: string;
  is_pinned?: boolean;
  is_system?: boolean;
  last_message_preview?: string | null;
  last_message_at?: string | null;
  unread?: number;
}): ChatListItem {
  const characterName = raw.character_name;
  const scenarioTitle = raw.scenario_title ?? null;
  const narratorName = raw.narrator_name ?? null;
  return {
    id: raw.id,
    characterId: raw.character_id,
    characterName,
    scenarioId: raw.scenario_id ?? null,
    scenarioTitle,
    narratorId: raw.narrator_id ?? null,
    narratorName,
    avatarUrl: raw.character_avatar_url || "",
    preview: formatChatPreview(raw.last_message_preview),
    time: formatChatTime(raw.last_message_at),
    unread: raw.unread ?? 0,
    isSystem: raw.is_system ?? false,
    isPinned: raw.is_pinned ?? false,
    displayName: raw.display_title || characterName,
  };
}

export function mapApiChatDetail(raw: {
  id: string;
  character_id: string;
  character_name: string;
  scenario_id?: string | null;
  scenario_title?: string | null;
  narrator_id?: string | null;
  narrator_name?: string | null;
  character_avatar_url?: string | null;
}): ChatListItem {
  const characterName = raw.character_name;
  const scenarioTitle = raw.scenario_title ?? null;
  const narratorName = raw.narrator_name ?? null;
  const parts = [characterName, scenarioTitle, narratorName].filter(Boolean);
  const displayName = parts.length > 1 ? parts.join(" · ") : characterName;
  return {
    id: raw.id,
    characterId: raw.character_id,
    characterName,
    scenarioId: raw.scenario_id ?? null,
    scenarioTitle,
    narratorId: raw.narrator_id ?? null,
    narratorName,
    avatarUrl: raw.character_avatar_url || "",
    preview: "",
    time: "",
    isPinned: false,
    displayName,
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
  upsertFromDetail: (raw: Parameters<typeof mapApiChatDetail>[0]) => void;
  getChat: (id: string) => ChatListItem | undefined;
  pinChat: (id: string) => Promise<void>;
  renameChat: (id: string, title: string) => Promise<void>;
  removeChat: (id: string) => Promise<void>;
}

const cachedChats = readChatsCache();

export const useChatsListStore = create<ChatsListState>((set, get) => ({
  chats: cachedChats ?? [],
  initialized: Boolean(cachedChats?.length),
  loading: false,

  load: async () => {
    const cached = readChatsCache();
    if (cached?.length) {
      set({ chats: sortChats(cached), initialized: true });
    }
    set({ loading: !cached?.length });
    try {
      const data = await chatService.list(1);
      const items = Array.isArray(data.items) ? data.items.map(mapApiChat) : [];
      const sorted = sortChats(items);
      writeChatsCache(sorted);
      set({ chats: sorted, initialized: true, loading: false });
    } catch {
      set((state) => ({
        chats: state.chats,
        initialized: true,
        loading: false,
      }));
    }
  },

  upsertFromDetail: (raw) => {
    const item = mapApiChatDetail(raw);
    const chats = get().chats.filter((c) => c.id !== item.id);
    set({ chats: sortChats([item, ...chats]), initialized: true });
  },

  getChat: (id) => get().chats.find((c) => c.id === id),

  pinChat: async (id) => {
    const chat = get().chats.find((c) => c.id === id);
    if (!chat) throw new Error("Chat not found");
    const pinned = !chat.isPinned;
    const raw = await chatListService.pin(id, pinned);
    const item = mapApiChat(raw);
    set({
      chats: sortChats(get().chats.map((c) => (c.id === id ? item : c))),
    });
  },

  renameChat: async (id, title) => {
    const trimmed = title.trim();
    if (!trimmed) return;
    const raw = await chatListService.rename(id, trimmed);
    const item = mapApiChat(raw);
    set({
      chats: sortChats(get().chats.map((c) => (c.id === id ? item : c))),
    });
  },

  removeChat: async (id) => {
    await chatListService.remove(id);
    set({ chats: get().chats.filter((c) => c.id !== id) });
    await get().load();
  },
}));
