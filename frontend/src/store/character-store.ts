import { create } from "zustand";

export interface Character {
  id: string;
  name: string;
  name_en?: string | null;
  slug: string;
  subtitle?: string;
  subtitle_en?: string | null;
  description: string;
  description_en?: string | null;
  greeting_message: string;
  avatar_url: string | null;
  preview_url: string | null;
  tags: string[];
  category: string;
  message_price: number;
  generation_price: number;
  is_nsfw: boolean;
  sort_order: number;
  personality_prompt?: string;
  behavior_params?: string[];
}

export interface CharacterScenario {
  id: string;
  character_id: string;
  title: string;
  title_en?: string | null;
  story: string;
  story_en?: string | null;
  communication_style: string;
  communication_style_en?: string | null;
  opening_message: string;
  opening_message_en?: string | null;
  sort_order: number;
}

interface CharacterState {
  characters: Character[];
  selectedCharacter: Character | null;
  setCharacters: (characters: Character[]) => void;
  setSelectedCharacter: (character: Character | null) => void;
}

export const useCharacterStore = create<CharacterState>((set) => ({
  characters: [],
  selectedCharacter: null,
  setCharacters: (characters) => set({ characters }),
  setSelectedCharacter: (character) => set({ selectedCharacter: character }),
}));
