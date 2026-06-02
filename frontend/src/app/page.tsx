"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { characterService } from "@/services/api";
import { CharacterCard } from "@/components/entities/CharacterCard";
import { CharacterCardSkeleton } from "@/components/shared/Skeleton";
import { useUserStore } from "@/store/user-store";
import { QUERY_KEYS } from "@/lib/constants";
import { formatGems } from "@/lib/utils";

export default function HomePage() {
  const { user } = useUserStore();
  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.characters,
    queryFn: () => characterService.list(),
  });

  return (
    <div className="px-4 pt-6 max-w-lg mx-auto">
      <motion.header
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <h1 className="text-2xl font-bold text-gradient">Veluna</h1>
        <p className="text-text-secondary text-sm mt-1">Choose your companion</p>
        {user && (
          <div className="flex items-center gap-1.5 mt-3 text-sm">
            <span>💎</span>
            <span className="text-accent font-semibold">{formatGems(user.gems)}</span>
            <span className="text-text-muted">gems</span>
          </div>
        )}
      </motion.header>

      <div className="grid grid-cols-2 gap-3">
        {isLoading
          ? Array.from({ length: 4 }).map((_, i) => <CharacterCardSkeleton key={i} />)
          : data?.items?.map((character: Parameters<typeof CharacterCard>[0]["character"], i: number) => (
              <CharacterCard key={character.id} character={character} index={i} />
            ))}
      </div>

      {!isLoading && !data?.items?.length && (
        <p className="text-center text-text-muted py-12">No characters available yet</p>
      )}
    </div>
  );
}
