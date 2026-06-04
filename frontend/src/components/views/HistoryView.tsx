"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { useNavStore } from "@/store/nav-store";
import { useMounted } from "@/hooks/use-mounted";
import { balanceService } from "@/services/api";
import { ensureTelegramSession, getApiError } from "@/lib/api-client";
import { QUERY_KEYS } from "@/lib/constants";
import { BackButton } from "@/components/shared/BackButton";
import { ListPanel } from "@/components/shared/ListPanel";
import { AnimeGemIcon, AnimeHeartIcon } from "@/components/icons/CurrencyIcons";
import { formatGems, cn } from "@/lib/utils";
import { chatBorderStyle, chatSeparatorStyle } from "@/lib/theme";

type HistoryTab = "expense" | "deposit";

const TABS: { id: HistoryTab; label: string }[] = [
  { id: "expense", label: "Траты" },
  { id: "deposit", label: "Пополнения" },
];

export function HistoryView() {
  const mounted = useMounted();
  const goBack = useNavStore((s) => s.goBack);
  const [tab, setTab] = useState<HistoryTab>("expense");

  const { data, isLoading, isError, error } = useQuery({
    queryKey: QUERY_KEYS.balanceHistory(tab),
    queryFn: async () => {
      await ensureTelegramSession();
      return balanceService.getHistory(tab);
    },
    retry: 2,
  });

  const items = data?.items ?? [];

  return (
    <div className="relative mx-auto max-w-lg px-4 pb-8 pt-5">
      <div className="mb-4 flex items-center gap-2">
        <BackButton onClick={goBack} />
        <h1 className="text-xl font-bold">История</h1>
      </div>

      <div className="mb-4 flex gap-1 rounded-2xl bg-bg-elevated/60 p-1" style={chatBorderStyle}>
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={cn(
              "relative flex-1 rounded-xl py-2.5 text-sm font-medium transition-all",
              tab === t.id ? "text-text-primary" : "text-text-muted hover:text-text-secondary"
            )}
          >
            {tab === t.id &&
              (mounted ? (
                <motion.div
                  layoutId="history-tab"
                  className="absolute inset-0 rounded-xl bg-bg-elevated"
                  style={chatBorderStyle}
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              ) : (
                <div
                  className="absolute inset-0 rounded-xl bg-bg-elevated"
                  style={chatBorderStyle}
                />
              ))}
            <span className="relative z-[1]">{t.label}</span>
          </button>
        ))}
      </div>

      {isError ? (
        <p className="py-12 text-center text-sm text-rose-300/90">
          {getApiError(error).message || "Не удалось загрузить историю"}
        </p>
      ) : isLoading ? (
        <ListPanel>
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-14 animate-pulse bg-bg-elevated/50"
              style={i < 3 ? chatSeparatorStyle : undefined}
            />
          ))}
        </ListPanel>
      ) : items.length === 0 ? (
        <p className="py-12 text-center text-sm text-text-muted">Пока нет записей</p>
      ) : (
        <ListPanel>
          {items.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className="flex items-center gap-3 px-4 py-3"
              style={i < items.length - 1 ? chatSeparatorStyle : undefined}
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-bg-elevated">
                {item.currency === "gems" ? (
                  <AnimeGemIcon className="h-5 w-5" />
                ) : (
                  <AnimeHeartIcon className="h-5 w-5" />
                )}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{item.description}</p>
                <p className="text-xs text-text-muted">
                  {new Date(item.created_at).toLocaleDateString("ru-RU", {
                    day: "numeric",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
              <span
                className={cn(
                  "shrink-0 text-sm font-semibold tabular-nums",
                  item.amount > 0 ? "text-emerald-400" : "text-text-primary"
                )}
              >
                {item.amount > 0 ? "+" : ""}
                {formatGems(Math.abs(item.amount))}
              </span>
            </motion.div>
          ))}
        </ListPanel>
      )}
    </div>
  );
}
