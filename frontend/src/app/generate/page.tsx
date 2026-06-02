"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { generationService } from "@/services/api";
import { Button } from "@/components/shared/Button";
import { Card } from "@/components/shared/Card";
import { useToast } from "@/hooks/use-toast";
import { QUERY_KEYS } from "@/lib/constants";
import { translateGenerationStatus } from "@/lib/i18n";

export default function GeneratePage() {
  const [prompt, setPrompt] = useState("");
  const { toast } = useToast();

  const { data: history } = useQuery({
    queryKey: QUERY_KEYS.generations,
    queryFn: () => generationService.list(),
  });

  const generate = useMutation({
    mutationFn: () => generationService.create({ prompt }),
    onSuccess: () => {
      toast("Генерация добавлена в очередь!", "success");
      setPrompt("");
    },
    onError: () => toast("Не удалось запустить генерацию", "error"),
  });

  return (
    <div className="mx-auto max-w-lg space-y-6 px-4 pb-28 pt-6">
      <motion.header initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 className="text-xl font-bold">Генерация</h1>
        <p className="mt-1 text-sm text-text-secondary">Создай AI-арт со своей waifu</p>
      </motion.header>

      <Card>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Опиши изображение, которое хочешь получить…"
          rows={4}
          className="w-full resize-none bg-transparent text-sm text-text-primary outline-none placeholder:text-text-muted"
        />
        <Button
          className="mt-3 w-full"
          loading={generate.isPending}
          disabled={!prompt.trim()}
          onClick={() => generate.mutate()}
        >
          Сгенерировать ✨
        </Button>
      </Card>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-text-secondary">Недавние</h2>
        <div className="grid grid-cols-2 gap-2">
          {history?.items?.map((gen: { id: string; status: string; image_url?: string; prompt: string }) => (
            <div key={gen.id} className="glass relative aspect-square overflow-hidden rounded-2xl">
              {gen.image_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={gen.image_url} alt={gen.prompt} className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-xs text-text-muted">
                  {translateGenerationStatus(gen.status)}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
