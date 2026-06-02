import { create } from "zustand";
import { persist } from "zustand/middleware";

interface SettingsState {
  language: string;
  notifications: boolean;
  nsfwEnabled: boolean;
  theme: "dark" | "light";
  setLanguage: (lang: string) => void;
  setNotifications: (enabled: boolean) => void;
  setNsfwEnabled: (enabled: boolean) => void;
  setTheme: (theme: "dark" | "light") => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      language: "en",
      notifications: true,
      nsfwEnabled: false,
      theme: "dark",
      setLanguage: (language) => set({ language }),
      setNotifications: (notifications) => set({ notifications }),
      setNsfwEnabled: (nsfwEnabled) => set({ nsfwEnabled }),
      setTheme: (theme) => set({ theme }),
    }),
    { name: "veluna-settings" }
  )
);
