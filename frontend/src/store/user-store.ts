import { create } from "zustand";

export interface User {
  id: string;
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  photo_url: string | null;
  language_code: string;
  locale_selected?: boolean;
  role: string;
  is_active: boolean;
  gems: number;
  created_at: string;
}

interface UserState {
  user: User | null;
  setUser: (user: User | null) => void;
  updateGems: (gems: number) => void;
}

export const useUserStore = create<UserState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  updateGems: (gems) =>
    set((state) => (state.user ? { user: { ...state.user, gems } } : state)),
}));
