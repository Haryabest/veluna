"use client";

import { Plus } from "lucide-react";
import { motion } from "framer-motion";
import { createPortal } from "react-dom";
import { useNavStore } from "@/store/nav-store";
import { STUDIO_GALLERY } from "@/lib/studio";
import { chatBorderStyle } from "@/lib/theme";

export function StudioView() {
  const openStudioCreate = useNavStore((s) => s.openStudioCreate);

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
          Создавай арты
        </h1>
        <p className="mt-1.5 text-sm text-text-secondary">и собирай свои арты</p>
      </motion.header>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.05 }}
        className="grid grid-cols-2 gap-3"
      >
        {STUDIO_GALLERY.map((art, i) => (
          <motion.div
            key={art.id}
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.04 }}
            className="aspect-square overflow-hidden rounded-2xl"
            style={chatBorderStyle}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={art.imageUrl} alt="" className="h-full w-full object-cover" />
          </motion.div>
        ))}
      </motion.div>

      {typeof document !== "undefined" &&
        createPortal(
          <button
            type="button"
            aria-label="Создать арт"
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
    </div>
  );
}
