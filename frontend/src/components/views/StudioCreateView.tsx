"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Grid3X3 } from "lucide-react";
import { BackButton } from "@/components/shared/BackButton";
import { AnimeGemIcon } from "@/components/icons/CurrencyIcons";
import { useNavStore } from "@/store/nav-store";
import { useToast } from "@/hooks/use-toast";
import { generationService } from "@/services/api";
import { ensureTelegramSession, getApiError } from "@/lib/api-client";
import {
  ASPECT_RATIOS,
  STUDIO_GENERATION_COST,
  STUDIO_MODELS,
  STUDIO_PROMPT_MAX,
  STUDIO_PROMPT_PLACEHOLDER,
  type AspectRatioId,
} from "@/lib/studio";
import { CHAT_BORDER } from "@/lib/theme";
import { cn } from "@/lib/utils";
import { logGeneration } from "@/lib/generation-log";

const SELECTED_BORDER = "2px solid #f472b6";
const SELECTED_GLOW = "0 0 14px rgba(244, 114, 182, 0.4)";

export function StudioCreateView() {
  const goBack = useNavStore((s) => s.goBack);
  const openStudioGenerating = useNavStore((s) => s.openStudioGenerating);
  const openStudioResult = useNavStore((s) => s.openStudioResult);
  const openStudioAllModels = useNavStore((s) => s.openStudioAllModels);
  const { toast } = useToast();
  const [prompt, setPrompt] = useState("");
  const [modelId, setModelId] = useState(STUDIO_MODELS[0]?.id ?? "miaomiao");
  const [aspectId, setAspectId] = useState<AspectRatioId>("1:1");
  const [loading, setLoading] = useState(false);

  const selectedModel = STUDIO_MODELS.find((m) => m.id === modelId) ?? STUDIO_MODELS[0];

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast("Опиши арт перед генерацией", "info");
      return;
    }
    setLoading(true);
    const finalPrompt = prompt.trim();
    logGeneration("start", { prompt: finalPrompt, model: selectedModel.name, aspect: aspectId });
    try {
      const authed = await ensureTelegramSession();
      if (!authed) {
        toast("Войдите через Telegram или обновите страницу на localhost", "error");
        return;
      }
      const [w, h] = aspectId.split(":").map(Number);
      const width = w >= h ? 1024 : 768;
      const height = h >= w ? 1024 : 768;

      openStudioGenerating();

      logGeneration("request", { prompt: finalPrompt, model: selectedModel.civitaiModelId, width, height });
      const result = await generationService.create({
        prompt: finalPrompt,
        model_id: selectedModel.civitaiModelId,
        width,
        height,
      });
      logGeneration("created", { id: result.id, status: result.status });

      openStudioResult(result.id);
    } catch (err: unknown) {
      const apiErr = getApiError(err);
      logGeneration("error", { error: apiErr.message, code: apiErr.code });
      toast(apiErr.message || "Ошибка генерации. Попробуй позже", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-lg px-4 pb-8 pt-4">
      <header className="mb-6 flex items-center gap-2">
        <BackButton onClick={goBack} />
        <h1 className="flex-1 text-center text-lg font-bold pr-9">Создание арта</h1>
      </header>

      <section className="mb-6">
        <label className="mb-2 block text-sm font-semibold text-text-primary">Опиши арт</label>
        <div
          className="relative rounded-2xl bg-bg-elevated/80 px-4 py-3"
          style={{ border: `1px solid ${CHAT_BORDER}` }}
        >
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value.slice(0, STUDIO_PROMPT_MAX))}
            placeholder={STUDIO_PROMPT_PLACEHOLDER}
            rows={5}
            className="w-full resize-none bg-transparent text-sm leading-relaxed text-text-primary outline-none placeholder:text-text-muted"
          />
          <span className="pointer-events-none absolute bottom-3 right-4 text-xs text-text-muted">
            {prompt.length}/{STUDIO_PROMPT_MAX}
          </span>
        </div>
      </section>

      <section className="mb-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-text-primary">Модель</h2>
          <button
            type="button"
            onClick={openStudioAllModels}
            className="flex items-center gap-1.5 rounded-xl bg-bg-elevated/60 px-3 py-1.5 text-xs font-medium text-text-secondary transition-colors hover:text-text-primary"
          >
            <Grid3X3 className="h-3.5 w-3.5" />
            Все модели
          </button>
        </div>
        <div className="flex gap-3 overflow-x-auto px-0.5 py-2 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {STUDIO_MODELS.map((model) => {
            const selected = modelId === model.id;
            return (
              <button
                key={model.id}
                type="button"
                onClick={() => setModelId(model.id)}
                className="flex shrink-0 flex-col items-center gap-2"
              >
                <div
                  className="h-[4.5rem] w-[4.5rem] shrink-0 rounded-2xl transition-all"
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
                      <span className="text-lg font-bold text-white/90">
                        {model.name.charAt(0)}
                      </span>
                    )}
                  </div>
                </div>
                <span
                  className={cn(
                    "text-xs font-medium",
                    selected ? "text-[#f9a8d4]" : "text-text-muted"
                  )}
                >
                  {model.name}
                </span>
              </button>
            );
          })}
        </div>
      </section>

      <section className="mb-8">
        <h2 className="mb-3 text-sm font-semibold text-text-primary">Соотношение сторон</h2>
        <div className="flex flex-col gap-2.5">
          {ASPECT_RATIOS.map((ratio) => {
            const selected = aspectId === ratio.id;
            const [w, h] = ratio.id.split(":").map(Number);
            const iconW = w >= h ? 28 : Math.round(28 * (w / h));
            const iconH = h >= w ? 28 : Math.round(28 * (h / w));

            return (
              <button
                key={ratio.id}
                type="button"
                onClick={() => setAspectId(ratio.id)}
                className="flex w-full items-center gap-4 rounded-2xl bg-bg-elevated/60 px-4 py-3.5 text-left transition-all"
                style={
                  selected
                    ? { border: SELECTED_BORDER, boxShadow: SELECTED_GLOW }
                    : { border: `1px solid ${CHAT_BORDER}` }
                }
              >
                <div
                  className="flex shrink-0 items-center justify-center rounded-lg bg-bg-elevated"
                  style={{
                    width: iconW + 16,
                    height: iconH + 16,
                    border: `1px solid ${CHAT_BORDER}`,
                  }}
                >
                  <div
                    className="rounded-sm bg-text-muted/30"
                    style={{ width: iconW, height: iconH }}
                  />
                </div>
                <div>
                  <p className="text-sm font-bold text-text-primary">{ratio.ratioLabel}</p>
                  <p className="text-xs text-text-muted">{ratio.label}</p>
                </div>
              </button>
            );
          })}
        </div>
      </section>

      <motion.button
        type="button"
        whileTap={{ scale: 0.98 }}
        onClick={handleGenerate}
        disabled={loading}
        className={cn(
          "studio-generate-btn flex w-full items-center justify-center gap-2 rounded-2xl py-4 text-base font-bold text-white",
          loading && "opacity-70"
        )}
      >
        {loading ? "Генерация..." : "Сгенерировать"} ({STUDIO_GENERATION_COST}{" "}
        <AnimeGemIcon className="h-5 w-5" />)
      </motion.button>
    </div>
  );
}
