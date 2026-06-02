"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import type { Character } from "@/store/character-store";
import { ROUTES } from "@/lib/constants";
import { cn, truncate } from "@/lib/utils";

interface CharacterCardProps {
  character: Character;
  index?: number;
}

export function CharacterCard({ character, index = 0 }: CharacterCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Link href={ROUTES.character(character.id)} className="block group">
        <div className="glass rounded-lg overflow-hidden transition-all duration-300 group-hover:glow-accent group-active:scale-[0.98]">
          <div className="aspect-[3/4] relative bg-bg-elevated">
            {character.preview_url || character.avatar_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={character.preview_url || character.avatar_url || ""}
                alt={character.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-4xl">
                🌸
              </div>
            )}
            {character.is_nsfw && (
              <span className="absolute top-2 right-2 text-[10px] bg-red-500/80 px-1.5 py-0.5 rounded-sm">
                18+
              </span>
            )}
          </div>
          <div className="p-3">
            <h3 className="font-semibold text-text-primary">{character.name}</h3>
            <p className="text-xs text-text-muted mt-0.5">{truncate(character.description, 60)}</p>
            <div className="flex gap-1 mt-2 flex-wrap">
              {character.tags.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className={cn("text-[10px] px-1.5 py-0.5 rounded-sm bg-bg-elevated text-text-secondary")}
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
