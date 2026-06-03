import { create } from "zustand";

export type AppTab = "home" | "studio" | "chats" | "profile";
export type AppScreen =
  | AppTab
  | "character"
  | "scenarios"
  | "chat"
  | "shop"
  | "history"
  | "topup"
  | "studio-create";

interface NavState {
  tab: AppTab;
  screen: AppScreen;
  characterId: string | null;
  chatId: string | null;
  setTab: (tab: AppTab) => void;
  openCharacter: (id: string) => void;
  openScenarios: () => void;
  openChat: (chatId: string) => void;
  openChatForCharacter: (characterId: string) => void;
  openShop: () => void;
  openHistory: () => void;
  openTopUp: () => void;
  openStudioCreate: () => void;
  goBack: () => void;
}

export const useNavStore = create<NavState>((set, get) => ({
  tab: "home",
  screen: "home",
  characterId: null,
  chatId: null,

  setTab: (tab) => set({ tab, screen: tab, characterId: null, chatId: null }),

  openCharacter: (characterId) => set({ screen: "character", characterId }),

  openScenarios: () => set({ screen: "scenarios" }),

  openChat: (chatId) => set({ screen: "chat", chatId, tab: "chats" }),

  openChatForCharacter: (characterId) => {
    const chatId = characterId === "0" ? "chat-4" : `chat-${characterId}`;
    set({ screen: "chat", chatId, tab: "chats", characterId: null });
  },

  openShop: () => set({ screen: "shop" }),

  openHistory: () => set({ screen: "history", tab: "profile" }),

  openTopUp: () => set({ screen: "topup", tab: "profile" }),

  openStudioCreate: () => set({ screen: "studio-create", tab: "studio" }),

  goBack: () => {
    const { screen, tab } = get();
    if (screen === "chat") {
      set({ screen: "chats", chatId: null });
    } else if (screen === "studio-create") {
      set({ screen: "studio" });
    } else if (screen === "history" || screen === "topup") {
      set({ screen: "profile" });
    } else if (screen === "shop") {
      set({ screen: tab });
    } else if (screen === "scenarios") {
      set({ screen: "character" });
    } else if (screen === "character") {
      set({ screen: tab, characterId: null });
    }
  },
}));

export function isMainTab(screen: AppScreen): screen is AppTab {
  return screen === "home" || screen === "studio" || screen === "chats" || screen === "profile";
}
