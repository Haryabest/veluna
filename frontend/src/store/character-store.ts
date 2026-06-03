import { create } from "zustand";

export interface Character {
  id: string;
  name: string;
  slug: string;
  subtitle?: string;
  description: string;
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
  story: string;
  communication_style: string;
  opening_message: string;
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
