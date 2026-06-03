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
  /** Screen to return to on goBack from history / topup */
  returnTo: AppScreen | null;
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
  returnTo: null,
  characterId: null,
  chatId: null,

  setTab: (tab) =>
    set({ tab, screen: tab, returnTo: null, characterId: null, chatId: null }),

  openCharacter: (characterId) => {
    const { screen } = get();
    set({
      screen: "character",
      characterId,
      returnTo: isMainTab(screen) ? screen : get().tab,
    });
  },

  openScenarios: () => set({ screen: "scenarios", returnTo: "character" }),

  openChat: (chatId) => set({ screen: "chat", chatId, tab: "chats", returnTo: "chats" }),

  openChatForCharacter: (characterId) => {
    const chatId = characterId === "0" ? "chat-4" : `chat-${characterId}`;
    set({ screen: "chat", chatId, tab: "chats", characterId: null, returnTo: "chats" });
  },

  openShop: () => {
    const { screen, tab } = get();
    set({
      screen: "shop",
      tab: isMainTab(screen) ? screen : tab,
      returnTo: isMainTab(screen) ? screen : tab,
    });
  },

  openHistory: () =>
    set({ screen: "history", tab: "profile", returnTo: "profile" }),

  openTopUp: () => {
    const { screen } = get();
    set({
      screen: "topup",
      tab: "profile",
      returnTo: screen,
    });
  },

  openStudioCreate: () => set({ screen: "studio-create", tab: "studio", returnTo: "studio" }),

  goBack: () => {
    const { screen, tab, returnTo } = get();

    if (screen === "chat") {
      set({ screen: "chats", chatId: null, returnTo: null });
      return;
    }
    if (screen === "studio-create") {
      set({ screen: "studio", returnTo: null });
      return;
    }
    if (screen === "history") {
      set({ screen: "profile", tab: "profile", returnTo: null });
      return;
    }
    if (screen === "topup") {
      const next =
        returnTo === "history"
          ? "history"
          : returnTo && isMainTab(returnTo)
            ? returnTo
            : "profile";
      set({ screen: next, tab: "profile", returnTo: null });
      return;
    }
    if (screen === "shop") {
      set({ screen: tab, returnTo: null });
      return;
    }
    if (screen === "scenarios") {
      set({ screen: "character", returnTo: returnTo ?? tab });
      return;
    }
    if (screen === "character") {
      set({ screen: returnTo && isMainTab(returnTo) ? returnTo : tab, characterId: null, returnTo: null });
      return;
    }
  },
}));

export function isMainTab(screen: AppScreen): screen is AppTab {
  return screen === "home" || screen === "studio" || screen === "chats" || screen === "profile";
}
