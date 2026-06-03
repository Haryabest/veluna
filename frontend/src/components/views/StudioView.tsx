"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/shared/Button";
import { ListPanel } from "@/components/shared/ListPanel";
import { Separator } from "@/components/shared/Separator";
import { chatBorderStyle, chatSeparatorStyle } from "@/lib/theme";

const MOCK_HISTORY = [
  { id: "1", prompt: "Акира на закате", imageUrl: "https://picsum.photos/seed/gen1/300/300", status: "done" },
  { id: "2", prompt: "Лунный дворец", imageUrl: "https://picsum.photos/seed/gen2/300/300", status: "done" },
  { id: "3", prompt: "Битва в академии", imageUrl: null, status: "pending" },
];

export function StudioView() {
  const [prompt, setPrompt] = useState("");

  return (
    <div className="mx-auto max-w-lg space-y-4 px-4 pt-6">
      <motion.header initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 className="text-xl font-bold">Студия</h1>
        <p className="mt-1 text-sm text-text-secondary">Создай AI-арт со своей waifu</p>
      </motion.header>

      <ListPanel>
        <div className="p-4">
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
        </div>
        <Separator />
        <p className="px-4 pt-3 text-xs font-semibold uppercase tracking-wide text-text-muted">
          Недавние
        </p>
        {MOCK_HISTORY.map((gen, i) => (
          <div
            key={gen.id}
            className="flex items-center gap-3 px-4 py-3"
            style={i < MOCK_HISTORY.length - 1 ? chatSeparatorStyle : undefined}
          >
            <div
              className="h-12 w-12 shrink-0 overflow-hidden rounded-lg bg-bg-elevated"
              style={chatBorderStyle}
            >
              {gen.imageUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={gen.imageUrl} alt="" className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-[10px] text-text-muted">
                  …
                </div>
              )}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{gen.prompt}</p>
              <p className="text-xs text-text-muted">
                {gen.status === "done" ? "Готово" : "В очереди"}
              </p>
            </div>
          </div>
        ))}
      </ListPanel>
    </div>
  );
}
