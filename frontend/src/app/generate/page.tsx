"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { generationService } from "@/services/api";
import { Button } from "@/components/shared/Button";
import { Card } from "@/components/shared/Card";
import { useToast } from "@/hooks/use-toast";
import { QUERY_KEYS } from "@/lib/constants";

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
      toast("Generation queued! Check back soon.", "success");
      setPrompt("");
    },
    onError: () => toast("Generation failed", "error"),
  });

  return (
    <div className="px-4 pt-6 max-w-lg mx-auto space-y-6">
      <motion.header initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 className="text-xl font-bold">Generate Image</h1>
        <p className="text-text-secondary text-sm mt-1">Create AI artwork with your waifu</p>
      </motion.header>

      <Card>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the image you want to generate..."
          rows={4}
          className="w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted outline-none resize-none"
        />
        <Button
          className="w-full mt-3"
          loading={generate.isPending}
          disabled={!prompt.trim()}
          onClick={() => generate.mutate()}
        >
          Generate ✨
        </Button>
      </Card>

      <section>
        <h2 className="text-sm font-semibold text-text-secondary mb-3">Recent</h2>
        <div className="grid grid-cols-2 gap-2">
          {history?.items?.map((gen: { id: string; status: string; image_url?: string; prompt: string }) => (
            <div key={gen.id} className="glass rounded-lg overflow-hidden aspect-square relative">
              {gen.image_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={gen.image_url} alt={gen.prompt} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-text-muted text-xs">
                  {gen.status}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
