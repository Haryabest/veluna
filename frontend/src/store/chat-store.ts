import { create } from "zustand";

export interface ChatMessage {
  id: string;
  chat_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  tokens_used: number;
  is_regenerated: boolean;
  created_at: string;
}

export interface Chat {
  id: string;
  character_id: string;
  status: string;
  message_count: number;
  last_message_at: string | null;
  created_at: string;
}

interface ChatState {
  chats: Chat[];
  activeChatId: string | null;
  messages: Record<string, ChatMessage[]>;
  isTyping: boolean;
  setChats: (chats: Chat[]) => void;
  setActiveChatId: (id: string | null) => void;
  setMessages: (chatId: string, messages: ChatMessage[]) => void;
  addMessage: (chatId: string, message: ChatMessage) => void;
  setIsTyping: (typing: boolean) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  chats: [],
  activeChatId: null,
  messages: {},
  isTyping: false,
  setChats: (chats) => set({ chats }),
  setActiveChatId: (id) => set({ activeChatId: id }),
  setMessages: (chatId, messages) =>
    set((state) => ({ messages: { ...state.messages, [chatId]: messages } })),
  addMessage: (chatId, message) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [chatId]: [...(state.messages[chatId] || []), message],
      },
    })),
  setIsTyping: (typing) => set({ isTyping: typing }),
}));
