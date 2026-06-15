"use client";

import { motion } from "framer-motion";
import { BackButton } from "@/components/shared/BackButton";
import { useCharacter } from "@/hooks/use-character";
import { useOpenScenarios } from "@/hooks/use-catalog-navigation";
import { useNavStore } from "@/store/nav-store";
import { useTranslation } from "@/hooks/use-translation";

export function CharacterDetailView() {
  const characterId = useNavStore((s) => s.characterId);
  const goBack = useNavStore((s) => s.goBack);
  const openScenarios = useOpenScenarios();
  const { character, isLoading, isError } = useCharacter(characterId);
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center px-4">
        <p className="text-text-muted">{t("character.loading")}</p>
      </div>
    );
  }

  if (!character) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center px-4">
        <p className="text-text-muted">
          {isError ? t("character.loadError") : t("character.notFound")}
        </p>
        <BackButton onClick={goBack} className="mt-4" />
      </div>
    );
  }

  const imageUrl = character.preview_url || character.avatar_url;
  const displayTags = (character.tags ?? []).filter(Boolean);

  return (
    <div className="relative mx-auto flex min-h-screen max-w-lg flex-col bg-bg-primary">
      <div className="relative h-[48vh] min-h-[300px] shrink-0 overflow-hidden bg-[#1a0b2e]">
        {imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={imageUrl}
            alt={character.name}
            className="absolute inset-0 h-full w-full object-cover object-top"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-[#2d1550] via-[#1a0b2e] to-bg-primary text-6xl">
            🌸
          </div>
        )}

        <div className="absolute inset-x-0 bottom-0 h-44 bg-gradient-to-t from-bg-primary via-bg-primary/90 to-transparent" />

        <div className="absolute inset-x-0 top-0 flex items-start px-4 pt-[max(0.75rem,env(safe-area-inset-top))]">
          <BackButton
            onClick={goBack}
            className="glass bg-black/25 text-white backdrop-blur-md"
            iconClassName="text-white"
          />
        </div>

        <div className="absolute inset-x-0 bottom-0 px-5 pb-5">
          <h1 className="text-[28px] font-bold leading-tight tracking-tight text-white drop-shadow-sm">
            {character.name}
          </h1>
          {character.subtitle && (
            <p className="mt-0.5 text-[15px] font-normal text-white/90">{character.subtitle}</p>
          )}
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-1 flex-col px-5 pt-5 pb-36"
      >
        {displayTags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {displayTags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-[#2a1548]/90 px-3.5 py-1.5 text-[13px] font-medium text-text-primary"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        <section className={displayTags.length > 0 ? "mt-5" : ""}>
          <h2 className="text-base font-bold text-text-primary">{t("character.about")}</h2>
          <p className="mt-2.5 text-[15px] leading-relaxed text-text-secondary">
            {character.description || "—"}
          </p>
        </section>
      </motion.div>

      <div className="fixed inset-x-0 bottom-0 z-40 mx-auto max-w-lg bg-gradient-to-t from-bg-primary via-bg-primary to-transparent px-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] pt-6">
        <button
          type="button"
          onClick={openScenarios}
          className="w-full rounded-2xl py-4 text-[17px] font-bold tracking-wide text-white shadow-[0_8px_32px_rgba(160,32,240,0.45)] transition-transform active:scale-[0.98]"
          style={{
            background: "linear-gradient(90deg, #9b8cff 0%, #e879f9 50%, #9333ea 100%)",
          }}
        >
          {t("character.play")}
        </button>
      </div>
    </div>
  );
}
