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
    onError: () => toast("Не удалось начать чат", "error"),
  });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-lg space-y-4 px-4 pt-6">
        <Skeleton className="aspect-[4/3] w-full rounded-2xl" />
        <Skeleton className="h-6 w-1/2" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  if (!character) {
    return <p className="py-12 text-center text-text-muted">Персонаж не найден</p>;
  }

  return (
    <div className="mx-auto max-w-lg pb-28">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <div className="relative aspect-[4/3] bg-bg-elevated">
          {character.preview_url || character.avatar_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={character.preview_url || character.avatar_url}
              alt={character.name}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-6xl">🌸</div>
          )}
        </div>

        <div className="space-y-4 px-4 py-5">
          <div>
            <h1 className="text-2xl font-bold">{character.name}</h1>
            <p className="mt-2 text-sm text-text-secondary">{character.description}</p>
          </div>

          <div className="flex flex-wrap gap-2">
            {character.tags?.map((tag: string) => (
              <span key={tag} className="glass rounded-full px-2.5 py-1 text-xs text-text-secondary">
                {tag}
              </span>
            ))}
          </div>

          <div className="glass rounded-2xl p-3 text-sm italic text-text-secondary">
            «{character.greeting_message}»
          </div>

          <div className="flex gap-4 text-sm text-text-muted">
            <span>💬 {formatGems(character.message_price)} гем/сообщ.</span>
            <span>✨ {formatGems(character.generation_price)} гем/ген.</span>
          </div>

          <Button
            className="w-full"
            size="lg"
            loading={startChat.isPending}
            onClick={() => startChat.mutate()}
          >
            Начать чат
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
