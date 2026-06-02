"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { characterService, chatService } from "@/services/api";
import { Button } from "@/components/shared/Button";
import { Skeleton } from "@/components/shared/Skeleton";
import { useToast } from "@/hooks/use-toast";
import { QUERY_KEYS, ROUTES } from "@/lib/constants";
import { formatGems } from "@/lib/utils";

export default function CharacterDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { toast } = useToast();

  const { data: character, isLoading } = useQuery({
    queryKey: QUERY_KEYS.character(id),
    queryFn: () => characterService.getById(id),
    enabled: !!id,
  });

  const startChat = useMutation({
    mutationFn: () => chatService.create(id),
    onSuccess: (chat) => {
      router.push(ROUTES.chat(chat.id));
    },
    onError: () => toast("Failed to start chat", "error"),
  });

  if (isLoading) {
    return (
      <div className="px-4 pt-6 max-w-lg mx-auto space-y-4">
        <Skeleton className="aspect-[4/3] w-full rounded-lg" />
        <Skeleton className="h-6 w-1/2" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  if (!character) {
    return <p className="text-center text-text-muted py-12">Character not found</p>;
  }

  return (
    <div className="max-w-lg mx-auto">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <div className="aspect-[4/3] relative bg-bg-elevated">
          {character.preview_url || character.avatar_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={character.preview_url || character.avatar_url}
              alt={character.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-6xl">🌸</div>
          )}
        </div>

        <div className="px-4 py-5 space-y-4">
          <div>
            <h1 className="text-2xl font-bold">{character.name}</h1>
            <p className="text-text-secondary text-sm mt-2">{character.description}</p>
          </div>

          <div className="flex gap-2 flex-wrap">
            {character.tags?.map((tag: string) => (
              <span key={tag} className="text-xs px-2 py-1 rounded-sm bg-bg-elevated text-text-secondary">
                {tag}
              </span>
            ))}
          </div>

          <div className="glass rounded-lg p-3 text-sm text-text-secondary italic">
            &ldquo;{character.greeting_message}&rdquo;
          </div>

          <div className="flex gap-4 text-sm text-text-muted">
            <span>💬 {formatGems(character.message_price)} gem/msg</span>
            <span>✨ {formatGems(character.generation_price)} gem/gen</span>
          </div>

          <Button
            className="w-full"
            size="lg"
            loading={startChat.isPending}
            onClick={() => startChat.mutate()}
          >
            Start Chat
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
