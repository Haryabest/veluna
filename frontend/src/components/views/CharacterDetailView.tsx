"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/shared/Button";
import { useNavStore } from "@/store/nav-store";
import { getMockCharacter } from "@/lib/mock-data";

function AppleBackButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Назад"
      className="flex h-9 w-9 items-center justify-center rounded-full border border-accent/20 bg-black/30 backdrop-blur-xl transition-transform active:scale-90"
    >
      <svg
        className="h-[18px] w-[18px] text-white"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden
      >
        <path d="M14.5 6.5L9 12l5.5 5.5" />
      </svg>
    </button>
  );
}

export function CharacterDetailView() {
  const characterId = useNavStore((s) => s.characterId);
  const goBack = useNavStore((s) => s.goBack);
  const openScenarios = useNavStore((s) => s.openScenarios);

  const character = characterId ? getMockCharacter(characterId) : null;

  if (!character) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center px-4">
        <p className="text-text-muted">Персонаж не найден</p>
        <Button variant="ghost" className="mt-4" onClick={goBack}>
          Назад
        </Button>
      </div>
    );
  }

  const imageUrl = character.preview_url || character.avatar_url;
  const subtitle = character.subtitle ?? character.tags[0];

  return (
    <div className="relative mx-auto flex min-h-screen max-w-lg flex-col bg-bg-primary">
      {/* Hero ~45% */}
      <div className="relative h-[45vh] min-h-[280px] shrink-0 overflow-hidden bg-bg-elevated">
        {imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={imageUrl}
            alt={character.name}
            className="absolute inset-0 h-full w-full object-cover object-top"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-6xl">🌸</div>
        )}

        {/* Fade into solid bg */}
        <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-bg-primary via-bg-primary/80 to-transparent" />

        {/* Name overlay on image */}
        <div className="absolute inset-x-0 bottom-0 px-5 pb-5">
          <h1 className="text-[28px] font-bold leading-tight tracking-tight text-white">
            {character.name}
          </h1>
          {subtitle && (
            <p className="mt-0.5 text-[15px] font-normal text-white/85">{subtitle}</p>
          )}
        </div>

        {/* Top bar */}
        <div className="absolute inset-x-0 top-0 flex items-start justify-between px-4 pt-[max(0.75rem,env(safe-area-inset-top))]">
          <AppleBackButton onClick={goBack} />
        </div>
      </div>

      {/* Content */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-1 flex-col px-5 pt-4 pb-36"
      >
        {character.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {character.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-xl bg-bg-elevated px-3.5 py-1.5 text-[13px] font-medium text-text-primary"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        <hr className="my-5 border-0 border-t border-accent/10" />

        <section className="flex-1">
          <h2 className="text-base font-bold text-text-primary">О персонаже</h2>
          <p className="mt-2.5 text-[15px] leading-relaxed text-text-secondary">
            {character.description}
          </p>
        </section>
      </motion.div>

      {/* Fixed gradient CTA */}
      <div className="fixed inset-x-0 bottom-0 z-40 mx-auto max-w-lg bg-gradient-to-t from-bg-primary via-bg-primary to-transparent px-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] pt-6">
        <button
          type="button"
          onClick={openScenarios}
          className="w-full rounded-2xl py-4 text-[17px] font-bold tracking-wide text-white shadow-[0_8px_32px_rgba(160,32,240,0.45)] transition-transform active:scale-[0.98]"
          style={{
            background: "linear-gradient(90deg, #9b8cff 0%, #b45cf0 45%, #9333ea 100%)",
          }}
        >
          ✨ ИГРАТЬ
        </button>
      </div>
    </div>
  );
}
