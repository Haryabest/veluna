"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { useNavStore } from "@/store/nav-store";
import { balanceService } from "@/services/api";
import { QUERY_KEYS } from "@/lib/constants";
import { BackButton } from "@/components/shared/BackButton";
import { AnimeGemIcon, AnimeHeartIcon } from "@/components/icons/CurrencyIcons";
import { formatGems, cn } from "@/lib/utils";
import { CHAT_BORDER } from "@/lib/theme";

type HistoryTab = "expense" | "deposit";

const TABS: { id: HistoryTab; label: string }[] = [
  { id: "expense", label: "Траты" },
  { id: "deposit", label: "Пополнения" },
];

export function HistoryView() {
  const goBack = useNavStore((s) => s.goBack);
  const [tab, setTab] = useState<HistoryTab>("expense");

  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.balanceHistory(tab),
    queryFn: () => balanceService.getHistory(tab),
  });

  const items = data?.items ?? [];

  return (
    <div className="relative mx-auto max-w-lg px-4 pb-8 pt-5">
      <div className="mb-4 flex items-center gap-2">
        <BackButton onClick={goBack} />
        <h1 className="text-xl font-bold">История</h1>
      </div>
      <div
        className="mb-5 flex gap-1 rounded-2xl bg-bg-elevated/60 p-1"
        style={{ border: `1px solid ${CHAT_BORDER}` }}
      >
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
            {tab === t.id && (
              <motion.div
                layoutId="history-tab"
                className="absolute inset-0 rounded-xl bg-bg-elevated"
                style={{ border: `1px solid ${CHAT_BORDER}` }}
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative z-[1]">{t.label}</span>
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass h-16 animate-pulse rounded-2xl" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <p className="py-12 text-center text-sm text-text-muted">Пока нет записей</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item, i) => (
            <motion.li
              key={item.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              className="glass flex items-center gap-3 rounded-2xl px-4 py-3"
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-bg-elevated/80">
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
            </motion.li>
          ))}
        </ul>
      )}
    </div>
  );
}
