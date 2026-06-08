import { create } from "zustand";

export type AppTab = "home" | "studio" | "chats" | "profile";
export type AppScreen =
  | AppTab
  | "character"
  | "scenarios"
  | "narrators"
  | "chat"
  | "shop"
  | "history"
  | "topup"
  | "studio-create"
  | "studio-generating"
  | "studio-result"
  | "studio-all-models";

interface NavState {
  tab: AppTab;
  screen: AppScreen;
  /** Screen to return to on goBack from history / topup */
  returnTo: AppScreen | null;
  characterId: string | null;
  scenarioId: string | null;
  chatId: string | null;
  setTab: (tab: AppTab) => void;
  openCharacter: (id: string) => void;
  openScenarios: () => void;
  openNarrators: (scenarioId: string) => void;
  openChat: (chatId: string) => void;
  openChatForCharacter: (characterId: string) => void;
  openShop: () => void;
  openHistory: () => void;
  openTopUp: () => void;
  openStudioCreate: () => void;
  openStudioGenerating: () => void;
  openStudioResult: (generationId: string) => void;
  openStudioAllModels: () => void;
  goToStudio: () => void;
  goBack: () => void;
  generationId: string | null;
  studioModelId: string | null;
  setStudioModelId: (id: string) => void;
}

export const useNavStore = create<NavState>((set, get) => ({
  tab: "home",
  screen: "home",
  returnTo: null,
  characterId: null,
  scenarioId: null,
  chatId: null,
  generationId: null,
  studioModelId: null,

  setStudioModelId: (id) => set({ studioModelId: id }),

  setTab: (tab) =>
    set({ tab, screen: tab, returnTo: null, characterId: null, scenarioId: null, chatId: null }),

  openCharacter: (characterId) => {
    const { screen } = get();
    set({
      screen: "character",
      characterId,
      scenarioId: null,
      returnTo: isMainTab(screen) ? screen : get().tab,
    });
  },

  openScenarios: () => set({ screen: "scenarios", returnTo: "character", scenarioId: null }),

  openNarrators: (scenarioId) => set({ screen: "narrators", scenarioId, returnTo: "scenarios" }),

  openChat: (chatId) => set({ screen: "chat", chatId, tab: "chats", returnTo: "chats" }),

  openChatForCharacter: (characterId) => {
    set({ screen: "scenarios", characterId, tab: "home", returnTo: "character" });
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

  openStudioGenerating: () => set({ screen: "studio-generating", tab: "studio", returnTo: "studio-create" }),

  openStudioResult: (generationId: string) => set({ screen: "studio-result", tab: "studio", generationId, returnTo: "studio" }),

  openStudioAllModels: () => set({ screen: "studio-all-models", tab: "studio", returnTo: "studio-create" }),

  goToStudio: () =>
    set({ screen: "studio", tab: "studio", generationId: null, returnTo: null, studioModelId: null }),

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
    if (screen === "studio-generating") {
      set({ screen: "studio-create", returnTo: null });
      return;
    }
    if (screen === "studio-result") {
      set({ screen: "studio", generationId: null, returnTo: null });
      return;
    }
    if (screen === "studio-all-models") {
      set({ screen: "studio-create", returnTo: null });
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
      set({ screen: "character", returnTo: returnTo ?? tab, scenarioId: null });
      return;
    }
    if (screen === "narrators") {
      set({ screen: "scenarios", returnTo: returnTo ?? "character" });
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
