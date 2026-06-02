"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/shared/Button";
import { Card } from "@/components/shared/Card";

const MOCK_HISTORY = [
  { id: "1", prompt: "Акира на закате", imageUrl: "https://picsum.photos/seed/gen1/300/300", status: "done" },
  { id: "2", prompt: "Лунный дворец", imageUrl: "https://picsum.photos/seed/gen2/300/300", status: "done" },
  { id: "3", prompt: "Битва в академии", imageUrl: null, status: "pending" },
];

export function StudioView() {
  const [prompt, setPrompt] = useState("");

  return (
    <div className="mx-auto max-w-lg space-y-6 px-4 pt-6">
      <motion.header initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 className="text-xl font-bold">Студия</h1>
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
        <Button className="mt-3 w-full" disabled={!prompt.trim()} onClick={() => setPrompt("")}>
          Сгенерировать ✨
        </Button>
      </Card>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-text-secondary">Недавние</h2>
        <div className="grid grid-cols-2 gap-2">
          {MOCK_HISTORY.map((gen) => (
            <div key={gen.id} className="glass relative aspect-square overflow-hidden rounded-2xl">
              {gen.imageUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={gen.imageUrl} alt={gen.prompt} className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-xs text-text-muted">
                  В очереди…
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
