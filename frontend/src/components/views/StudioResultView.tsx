"use client";

import { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { BackButton } from "@/components/shared/BackButton";
import { useNavStore } from "@/store/nav-store";
import { generationService } from "@/services/api";
import { getApiError } from "@/lib/api-client";
import { QUERY_KEYS } from "@/lib/constants";
import { chatBorderStyle } from "@/lib/theme";
import { translateGenerationStatus } from "@/lib/i18n";
import { logGeneration } from "@/lib/generation-log";

const POLL_STATUSES = new Set(["pending", "processing"]);

function isInProgress(status: string | undefined) {
  return status != null && POLL_STATUSES.has(status);
}

export function StudioResultView() {
  const generationId = useNavStore((s) => s.generationId);
  const goBack = useNavStore((s) => s.goBack);
  const setTab = useNavStore((s) => s.setTab);

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
    return (
      <ResultError
        message={msg}
        onBack={goBack}
      />
    );
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
          <p className="mt-4 line-clamp-3 text-center text-xs text-text-muted">{data.prompt}</p>
        ) : null}

        <motion.button
          type="button"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setTab("studio")}
          className="mt-6 w-full rounded-2xl py-3.5 text-sm font-bold uppercase tracking-wider text-white"
          style={{
            background: "linear-gradient(135deg, #f9a8d4 0%, #ec4899 50%, #c084fc 100%)",
          }}
        >
          Вернуться в студию
        </motion.button>
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
