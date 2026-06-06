"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Share2, X } from "lucide-react";
import { BackButton } from "@/components/shared/BackButton";
import { useToast } from "@/hooks/use-toast";
import { getApiError } from "@/lib/api-client";
import { shareArtImage } from "@/lib/share-art";
import { chatBorderStyle } from "@/lib/theme";
import { cn } from "@/lib/utils";

type Props = {
  art: { id: string; imageUrl: string; prompt?: string } | null;
  onClose: () => void;
};

export function StudioArtViewer({ art, onClose }: Props) {
  const { toast } = useToast();
  const [sharing, setSharing] = useState(false);

  const handleShare = async () => {
    if (!art?.imageUrl) return;
    setSharing(true);
    try {
      await shareArtImage(art.imageUrl, art.id);
    } catch (err) {
      toast(getApiError(err).message || "Не удалось поделиться", "error");
    } finally {
      setSharing(false);
    }
  };

  return (
    <AnimatePresence>
      {art ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[70] flex flex-col bg-bg-base/95 backdrop-blur-md"
        >
          <header className="relative z-10 flex shrink-0 items-center gap-2 px-4 pb-2 pt-[max(0.75rem,env(safe-area-inset-top))]">
            <BackButton onClick={onClose} />
            <h1 className="flex-1 text-center text-lg font-bold pr-9">Арт</h1>
          </header>

          <div className="relative z-10 flex flex-1 flex-col overflow-y-auto px-4 pb-8">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="overflow-hidden rounded-2xl bg-bg-elevated/80"
              style={chatBorderStyle}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={art.imageUrl} alt="" className="w-full object-contain" />
            </motion.div>

            {art.prompt ? (
              <p className="mt-4 text-center text-sm text-text-secondary">{art.prompt}</p>
            ) : null}

            <div className="mt-6 flex flex-col gap-3">
              <button
                type="button"
                onClick={handleShare}
                disabled={sharing}
                className={cn(
                  "flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 text-sm font-semibold text-white",
                  sharing && "opacity-70"
                )}
                style={{
                  background: "linear-gradient(135deg, #f9a8d4 0%, #ec4899 100%)",
                }}
              >
                <Share2 className="h-4 w-4" />
                {sharing ? "Открываю…" : "Поделиться"}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="w-full rounded-2xl bg-bg-elevated/80 py-3.5 text-sm font-semibold text-text-primary"
                style={chatBorderStyle}
              >
                Закрыть
              </button>
            </div>
          </div>

          <button
            type="button"
            aria-label="Закрыть"
            onClick={onClose}
            className="absolute right-4 top-[max(0.75rem,env(safe-area-inset-top))] z-20 flex h-9 w-9 items-center justify-center rounded-full bg-bg-elevated/80 text-text-muted md:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
