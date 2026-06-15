"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { motion } from "framer-motion";
import { createPortal } from "react-dom";
import { useNavStore } from "@/store/nav-store";
import { generationService } from "@/services/api";
import { QUERY_KEYS } from "@/lib/constants";
import { chatBorderStyle } from "@/lib/theme";
import { StudioArtViewer } from "@/components/studio/StudioArtViewer";
import { useTranslation } from "@/hooks/use-translation";

export function StudioView() {
  const { t } = useTranslation();
  const screen = useNavStore((s) => s.screen);
  const tab = useNavStore((s) => s.tab);
  const openStudioCreate = useNavStore((s) => s.openStudioCreate);
  const [viewerArt, setViewerArt] = useState<{
    id: string;
    imageUrl: string;
    prompt?: string;
  } | null>(null);
  const showFab = tab === "studio" && screen === "studio" && !viewerArt;

  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.generations,
    queryFn: () => generationService.list(1),
    staleTime: 20_000,
  });

  const gallery = useMemo(() => {
    const items = data?.items;
    if (!Array.isArray(items)) return [];
    return items
      .filter((g: { image_url?: string | null; status?: string }) => g.image_url && g.status === "completed")
      .map(
        (g: {
          id: string;
          image_url: string;
          thumbnail_url?: string | null;
          prompt?: string;
        }) => ({
          id: g.id,
          imageUrl: g.thumbnail_url || g.image_url,
          prompt: g.prompt ?? "",
        })
      );
  }, [data]);

  return (
    <div className="relative mx-auto max-w-lg px-4 pb-36 pt-6">
      <motion.header
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 text-center"
      >
        <h1
          className="text-2xl font-bold tracking-tight"
          style={{
            background: "linear-gradient(90deg, #f9a8d4 0%, #e879f9 35%, #c084fc 70%, #a78bfa 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          {t("studio.title")}
        </h1>
        <p className="mt-1.5 text-sm text-text-secondary">{t("studio.subtitle")}</p>
      </motion.header>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.05 }}
        className="grid grid-cols-2 gap-3"
      >
        {isLoading ? (
          <p className="col-span-2 py-12 text-center text-sm text-text-muted">{t("common.loading")}</p>
        ) : gallery.length === 0 ? (
          <p className="col-span-2 py-12 text-center text-sm text-text-muted">
            {t("studio.empty")}
          </p>
        ) : (
        gallery.map((art, i) => (
          <motion.button
            key={art.id}
            type="button"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.04 }}
            onClick={() => setViewerArt(art)}
            className="aspect-square overflow-hidden rounded-2xl text-left active:scale-[0.98]"
            style={chatBorderStyle}
            aria-label={art.prompt ? t("studio.artLabel", { prompt: art.prompt }) : t("studio.openArt")}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={art.imageUrl} alt="" className="h-full w-full object-cover" />
          </motion.button>
        ))
        )}
      </motion.div>

      {showFab &&
        typeof document !== "undefined" &&
        createPortal(
          <button
            type="button"
            aria-label={t("studio.createArt")}
            onClick={openStudioCreate}
            className="studio-fab-gradient pointer-events-auto fixed left-1/2 z-[60] flex h-[4.25rem] w-[4.25rem] -translate-x-1/2 items-center justify-center rounded-full text-white transition-transform active:scale-95"
            style={{
              bottom: "calc(6.75rem + env(safe-area-inset-bottom, 0px))",
            }}
          >
            <Plus className="h-9 w-9" strokeWidth={2.5} aria-hidden />
          </button>,
          document.body
        )}

      <StudioArtViewer art={viewerArt} onClose={() => setViewerArt(null)} />
    </div>
  );
}
