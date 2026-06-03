"use client";

import { motion } from "framer-motion";
import type { Character } from "@/store/character-store";
import { useNavStore } from "@/store/nav-store";
import { truncate } from "@/lib/utils";

interface CharacterCardProps {
  character: Character;
  index?: number;
}

export function CharacterCard({ character, index = 0 }: CharacterCardProps) {
  const openCharacter = useNavStore((s) => s.openCharacter);
  const imageUrl = character.preview_url || character.avatar_url;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.35 }}
      className="h-full"
    >
      <button
        type="button"
        onClick={() => openCharacter(character.id)}
        className="group block h-full w-full text-left"
      >
        <div className="glass relative aspect-[3/4] overflow-hidden rounded-2xl transition-transform duration-300 active:scale-[0.97] group-hover:shadow-glow">
          {imageUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={imageUrl}
              alt={character.name}
              className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
          ) : (
            <div className="absolute inset-0 bg-gradient-to-br from-accent-deep via-accent/40 to-bg-secondary" />
          )}

          <div className="absolute inset-0 bg-gradient-to-t from-bg-primary via-bg-primary/40 to-transparent" />

          {character.is_nsfw && (
            <span className="glass absolute right-2 top-2 rounded-full px-2 py-0.5 text-[10px] font-semibold text-accent-light">
              18+
            </span>
          )}

          <div className="absolute inset-x-0 bottom-0 p-3">
            <h3 className="text-sm font-bold leading-tight text-text-primary">{character.name}</h3>
            <p className="mt-0.5 line-clamp-2 text-[11px] leading-snug text-text-secondary">
              {character.subtitle || truncate(character.description, 72)}
            </p>
          </div>
        </div>
      </button>
    </motion.div>
  );
}
