"use client";

import { useEffect, useState } from "react";
import { Grid3X3, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { AnimeGemIcon } from "@/components/icons/CurrencyIcons";
import { useToast } from "@/hooks/use-toast";
import { useTranslation } from "@/hooks/use-translation";
import { generationService } from "@/services/api";
import { ensureTelegramSession, getApiError } from "@/lib/api-client";
import {
  ALL_STUDIO_MODELS,
  buildStudioPrompt,
  findStudioModel,
  getStudioModelLabel,
  getStudioPromptPlaceholder,
  STUDIO_GENERATION_COST,
  STUDIO_MODELS,
  STUDIO_PROMPT_MAX,
} from "@/lib/studio";
import { ArtSceneBackground } from "@/components/shared/ArtSceneBackground";
import { CHAT_BORDER } from "@/lib/theme";
import { cn } from "@/lib/utils";

const SELECTED_BORDER = "2px solid #f472b6";
const SELECTED_GLOW = "0 0 14px rgba(244, 114, 182, 0.4)";

type Props = {
  open: boolean;
  characterId: string;
  characterName: string;
  generationCost?: number;
  onClose: () => void;
  onStarted: (generationId: string) => void;
};

export function ChatPhotoGenerateModal({
  open,
  characterId,
  characterName,
  generationCost = STUDIO_GENERATION_COST,
  onClose,
  onStarted,
}: Props) {
  const { t, locale } = useTranslation();
  const { toast } = useToast();
  const [prompt, setPrompt] = useState("");
  const [modelId, setModelId] = useState(STUDIO_MODELS[0]?.id ?? "miaomiao");
  const [showAllModels, setShowAllModels] = useState(false);
  const [loading, setLoading] = useState(false);

  const models = showAllModels ? ALL_STUDIO_MODELS : STUDIO_MODELS;
  const selectedModel =
    findStudioModel(modelId) ?? STUDIO_MODELS.find((m) => m.id === modelId) ?? STUDIO_MODELS[0];

  useEffect(() => {
    if (!open) {
      setShowAllModels(false);
      setPrompt("");
    }
  }, [open]);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast(t("chat.photoGen.promptRequired"), "info");
      return;
    }
    setLoading(true);
    try {
      const authed = await ensureTelegramSession();
      if (!authed) {
        toast(t("chat.photoGen.loginRequired"), "error");
        return;
      }

      const finalPrompt = buildStudioPrompt(selectedModel, prompt);

      const result = await generationService.create({
        prompt: finalPrompt,
        character_id: characterId,
        model_id: selectedModel.id,
        width: 768,
        height: 768,
      });

      onStarted(result.id);
      onClose();
    } catch (err: unknown) {
      toast(getApiError(err).message || t("studio.create.error"), "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        >
          <ArtSceneBackground />
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 320 }}
            className="relative z-10 max-h-[88vh] w-full max-w-lg overflow-y-auto rounded-t-3xl bg-bg-base/95 px-4 pb-8 pt-5 backdrop-blur-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-bold">{t("chat.photoGen.title")}</h2>
              <button
                type="button"
                onClick={onClose}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-bg-elevated text-text-muted"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <p className="mb-4 text-sm text-text-secondary">
              {t("chat.photoGen.hint", {
                name: characterName,
                style: getStudioModelLabel(selectedModel, locale),
              })}
            </p>

            <label className="mb-2 block text-sm font-semibold text-text-primary">{t("chat.photoGen.promptLabel")}</label>
            <div
              className="relative mb-5 rounded-2xl bg-bg-elevated/80 px-4 py-3"
              style={{ border: `1px solid ${CHAT_BORDER}` }}
            >
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value.slice(0, STUDIO_PROMPT_MAX))}
                placeholder={getStudioPromptPlaceholder(locale)}
                rows={4}
                className="w-full resize-none bg-transparent text-sm leading-relaxed text-text-primary outline-none placeholder:text-text-muted"
              />
              <span className="pointer-events-none absolute bottom-3 right-4 text-xs text-text-muted">
                {prompt.length}/{STUDIO_PROMPT_MAX}
              </span>
            </div>

            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text-primary">{t("common.model")}</h3>
              <button
                type="button"
                onClick={() => setShowAllModels((v) => !v)}
                className="flex items-center gap-1.5 rounded-xl bg-bg-elevated/60 px-3 py-1.5 text-xs font-medium text-text-secondary"
              >
                <Grid3X3 className="h-3.5 w-3.5" />
                {showAllModels ? t("common.mainModels") : t("common.allModels")}
              </button>
            </div>

            <div className="mb-6 flex gap-3 overflow-x-auto py-2 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
              {models.map((model) => {
                const selected = modelId === model.id;
                return (
                  <button
                    key={model.id}
                    type="button"
                    onClick={() => setModelId(model.id)}
                    className="flex shrink-0 flex-col items-center gap-2"
                  >
                    <div
                      className="h-16 w-16 shrink-0 rounded-2xl transition-all"
                      style={
                        selected
                          ? {
                              padding: 2,
                              background: "linear-gradient(135deg, #f9a8d4 0%, #ec4899 100%)",
                              boxShadow: SELECTED_GLOW,
                            }
                          : { border: `1px solid ${CHAT_BORDER}` }
                      }
                    >
                      <div className="flex h-full w-full items-center justify-center overflow-hidden rounded-[14px] bg-gradient-to-br from-accent-deep/80 to-accent/40">
                        {model.imageUrl ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img src={model.imageUrl} alt="" className="h-full w-full object-cover" />
                        ) : (
                          <span className="text-sm font-bold text-white/90">{model.name.charAt(0)}</span>
                        )}
                      </div>
                    </div>
                    <span
                      className={cn(
                        "max-w-[4.5rem] truncate text-[10px] font-medium",
                        selected ? "text-[#f9a8d4]" : "text-text-muted"
                      )}
                    >
                      {getStudioModelLabel(model, locale)}
                    </span>
                  </button>
                );
              })}
            </div>

            <button
              type="button"
              onClick={handleGenerate}
              disabled={loading}
              className={cn(
                "flex w-full items-center justify-center gap-2 rounded-2xl py-4 text-base font-bold text-white",
                loading && "opacity-70"
              )}
              style={{
                background: "linear-gradient(135deg, #b45cf0 0%, #7c3aed 50%, #6d28d9 100%)",
              }}
            >
              {loading ? t("chat.photoGen.generating") : (
                <>
                  {t("studio.create.submit")} ({generationCost} <AnimeGemIcon className="h-5 w-5" />)
                </>
              )}
            </button>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
