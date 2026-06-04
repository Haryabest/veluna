"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Share2, Sparkles } from "lucide-react";
import { BackButton } from "@/components/shared/BackButton";
import { useNavStore } from "@/store/nav-store";
import { useToast } from "@/hooks/use-toast";
import { generationService } from "@/services/api";
import { ensureTelegramSession, getApiError } from "@/lib/api-client";
import { QUERY_KEYS } from "@/lib/constants";
import { chatBorderStyle } from "@/lib/theme";
import { translateGenerationStatus } from "@/lib/i18n";
import { logGeneration } from "@/lib/generation-log";
import {
  canShareViaTelegram,
  getTelegramBotLink,
  openTelegramTextShare,
  sharePreparedTelegramMessage,
} from "@/lib/telegram-share";
import { cn } from "@/lib/utils";

const POLL_STATUSES = new Set(["pending", "processing"]);

function isInProgress(status: string | undefined) {
  return status != null && POLL_STATUSES.has(status);
}

export function StudioResultView() {
  const generationId = useNavStore((s) => s.generationId);
  const goBack = useNavStore((s) => s.goBack);
  const goToStudio = useNavStore((s) => s.goToStudio);
  const { toast } = useToast();
  const [sharing, setSharing] = useState(false);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: [...QUERY_KEYS.generations, generationId] as const,
    queryFn: () => {
      if (!generationId) throw new Error("Нет id генерации");
      logGeneration("poll", { id: generationId });
      return generationService.getById(generationId);
    },
    enabled: Boolean(generationId),
    refetchInterval: (query) => (isInProgress(query.state.data?.status) ? 2500 : false),
    retry: 3,
    retryDelay: 1500,
  });

  const status = data?.status as string | undefined;
  const imageUrl = (data?.image_url ?? data?.thumbnail_url) as string | null | undefined;
  const loggedStatusRef = useRef<string | null>(null);

  useEffect(() => {
    if (!generationId || !status) return;
    if (loggedStatusRef.current === status) return;
    if (status === "completed") {
      loggedStatusRef.current = status;
      logGeneration("completed", { id: generationId });
    } else if (status === "failed" || status === "moderated") {
      loggedStatusRef.current = status;
      logGeneration("error", { id: generationId, status });
    }
  }, [generationId, status]);

  const handleShare = useCallback(async () => {
    if (!imageUrl || !generationId) {
      toast("Изображение ещё не готово", "info");
      return;
    }
    if (!canShareViaTelegram()) {
      toast("Поделиться можно только в Telegram Mini App", "info");
      return;
    }

    setSharing(true);
    logGeneration("share", { id: generationId, url: imageUrl });
    try {
      await ensureTelegramSession();
      const prepared = await generationService.prepareShare(generationId);
      const botLink = getTelegramBotLink(prepared.bot_link);
      const shared = await sharePreparedTelegramMessage(prepared.prepared_message_id);
      if (!shared) {
        openTelegramTextShare(botLink);
      }
    } catch (err: unknown) {
      const msg = getApiError(err).message;
      logGeneration("error", { action: "share", error: msg });
      try {
        openTelegramTextShare(getTelegramBotLink());
      } catch {
        toast(msg || "Не удалось поделиться", "error");
      }
    } finally {
      setSharing(false);
    }
  }, [generationId, imageUrl, toast]);

  if (!generationId) {
    return (
      <div className="mx-auto max-w-lg px-4 pb-8 pt-4">
        <header className="mb-6 flex items-center gap-2">
          <BackButton onClick={goBack} />
          <h1 className="flex-1 text-center text-lg font-bold pr-9">Результат</h1>
        </header>
        <p className="text-center text-sm text-text-secondary">Генерация не найдена</p>
      </div>
    );
  }

  if (isLoading && !data) {
    return <ResultLoader subtitle={translateGenerationStatus("processing")} />;
  }

  if (isError) {
    const msg = getApiError(error).message || "Ошибка загрузки результата";
    logGeneration("error", { id: generationId, error: msg });
    return <ResultError message={msg} onBack={goBack} />;
  }

  if (isInProgress(status)) {
    return <ResultLoader subtitle={translateGenerationStatus(status ?? "processing")} />;
  }

  if (status === "failed" || status === "moderated") {
    return (
      <ResultError
        message={
          status === "moderated"
            ? "Изображение не прошло модерацию"
            : data?.error_message || "Генерация не удалась. Попробуй снова"
        }
        onBack={goBack}
      />
    );
  }

  if (status === "completed" && imageUrl) {
    return (
      <div className="mx-auto max-w-lg px-4 pb-8 pt-4">
        <header className="mb-6 flex items-center gap-2">
          <BackButton onClick={goBack} />
          <h1 className="flex-1 text-center text-lg font-bold pr-9">Готово</h1>
        </header>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="overflow-hidden rounded-2xl bg-bg-elevated/80"
          style={chatBorderStyle}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={imageUrl} alt="" className="w-full object-contain" />
        </motion.div>

        {data?.prompt ? (
          <p className="mt-4 text-center text-sm text-text-secondary">{data.prompt}</p>
        ) : null}

        <div className="mt-6 flex flex-col gap-3">
          <button
            type="button"
            onClick={handleShare}
            disabled={sharing}
            className={cn(
              "flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 text-sm font-semibold text-white transition-opacity",
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
            onClick={goToStudio}
            className="w-full rounded-2xl bg-bg-elevated/80 py-3.5 text-sm font-semibold text-text-primary transition-colors hover:bg-bg-elevated"
            style={chatBorderStyle}
          >
            Вернуться в студию
          </button>
        </div>
      </div>
    );
  }

  return <ResultLoader subtitle={translateGenerationStatus(status ?? "pending")} />;
}

function ResultLoader({ subtitle }: { subtitle: string }) {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center px-6">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="mb-6 flex h-24 w-24 items-center justify-center rounded-full"
        style={{
          background: "linear-gradient(135deg, #f9a8d4 0%, #e879f9 50%, #c084fc 100%)",
          boxShadow: "0 0 48px rgba(232, 121, 249, 0.45)",
        }}
      >
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 3, ease: "linear" }}>
          <Sparkles className="h-12 w-12 text-white" strokeWidth={1.5} />
        </motion.div>
      </motion.div>
      <p className="text-lg font-bold text-text-primary">Создаю арт</p>
      <p className="mt-2 text-sm text-text-secondary">{subtitle}</p>
      <div className="mt-8 flex gap-1.5">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="h-2 w-2 rounded-full bg-accent-light"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ repeat: Infinity, duration: 1.2, delay: i * 0.2 }}
          />
        ))}
      </div>
    </div>
  );
}

function ResultError({ message, onBack }: { message: string; onBack: () => void }) {
  return (
    <div className="mx-auto max-w-lg px-4 pb-8 pt-4">
      <header className="mb-6 flex items-center gap-2">
        <BackButton onClick={onBack} />
        <h1 className="flex-1 text-center text-lg font-bold pr-9">Ошибка</h1>
      </header>
      <div
        className="rounded-2xl bg-bg-elevated/80 px-4 py-8 text-center"
        style={chatBorderStyle}
      >
        <p className="text-sm text-text-secondary">{message}</p>
      </div>
    </div>
  );
}
