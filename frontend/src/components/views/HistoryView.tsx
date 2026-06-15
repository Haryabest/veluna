"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { useNavStore } from "@/store/nav-store";
import { useMounted } from "@/hooks/use-mounted";
import { balanceService, userService } from "@/services/api";
import { ensureTelegramSession, getApiError } from "@/lib/api-client";
import { QUERY_KEYS } from "@/lib/constants";
import { BackButton } from "@/components/shared/BackButton";
import { ListPanel } from "@/components/shared/ListPanel";
import { HistoryRowSkeleton } from "@/components/shared/Skeleton";
import { AnimeGemIcon, AnimeHeartIcon } from "@/components/icons/CurrencyIcons";
import { formatGems, cn } from "@/lib/utils";
import { chatBorderStyle, chatSeparatorStyle } from "@/lib/theme";
import { useTranslation } from "@/hooks/use-translation";
import type { TranslationKey } from "@/lib/i18n/translations";

type HistoryTab = "expense" | "deposit";

const TAB_KEYS: { id: HistoryTab; labelKey: TranslationKey }[] = [
  { id: "expense", labelKey: "history.expense" },
  { id: "deposit", labelKey: "history.deposit" },
];

export function HistoryView() {
  const mounted = useMounted();
  const goBack = useNavStore((s) => s.goBack);
  const { t, locale } = useTranslation();
  const [tab, setTab] = useState<HistoryTab>("expense");

  const { data, isLoading, isError, error } = useQuery({
    queryKey: [...QUERY_KEYS.balanceHistory(tab), locale],
    queryFn: async () => {
      await ensureTelegramSession();
      return balanceService.getHistory(tab);
    },
    retry: 2,
  });

  const { data: finance } = useQuery({
    queryKey: QUERY_KEYS.financeStats,
    queryFn: async () => {
      await ensureTelegramSession();
      return userService.getFinanceStats();
    },
    staleTime: 60_000,
  });

  const items = data?.items ?? [];

  return (
    <div className="relative mx-auto max-w-lg px-4 pb-8 pt-5">
      <div className="mb-4 flex items-center gap-2">
        <BackButton onClick={goBack} />
        <h1 className="text-xl font-bold">{t("history.title")}</h1>
      </div>

      {finance ? (
        <div className="mb-4 space-y-2">
          <div
            className="rounded-2xl bg-bg-elevated/60 px-4 py-3"
            style={chatBorderStyle}
          >
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-text-muted">
              {t("history.balance")}
            </p>
            <div className="flex items-center gap-4 text-sm font-semibold text-text-primary">
              <span className="inline-flex items-center gap-1.5">
                {formatGems(finance.balance.gems)}
                <AnimeGemIcon className="h-4 w-4" />
              </span>
              <span className="inline-flex items-center gap-1.5">
                {formatGems(finance.balance.credits)}
                <AnimeHeartIcon className="h-4 w-4" />
              </span>
            </div>
          </div>

          <div
            className="grid grid-cols-2 gap-2 rounded-2xl bg-bg-elevated/60 p-3"
            style={chatBorderStyle}
          >
            <FinanceStatCell
              label={t("profile.spent")}
              gems={finance.spent.gems}
              credits={finance.spent.credits}
              negative
            />
            <FinanceStatCell
              label={t("profile.deposited")}
              gems={finance.deposited.gems}
              credits={finance.deposited.credits}
            />
          </div>

          {finance.purchases.completed_count > 0 ? (
            <div
              className="rounded-2xl bg-bg-elevated/60 px-4 py-3 text-xs text-text-muted"
              style={chatBorderStyle}
            >
              {t("history.purchases")}{" "}
              <span className="font-semibold text-text-secondary">{finance.purchases.completed_count}</span>
              {finance.purchases.stars_total > 0 ? (
                <span className="ml-2">· ⭐ {formatGems(finance.purchases.stars_total)}</span>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="mb-4 flex gap-1 rounded-2xl bg-bg-elevated/60 p-1" style={chatBorderStyle}>
        {TAB_KEYS.map((tabItem) => (
          <button
            key={tabItem.id}
            type="button"
            onClick={() => setTab(tabItem.id)}
            className={cn(
              "relative flex-1 rounded-xl py-2.5 text-sm font-medium transition-all",
              tab === tabItem.id ? "text-text-primary" : "text-text-muted hover:text-text-secondary"
            )}
          >
            {tab === tabItem.id &&
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
            <span className="relative z-[1]">{t(tabItem.labelKey)}</span>
          </button>
        ))}
      </div>

      {isError ? (
        <p className="py-12 text-center text-sm text-rose-300/90">
          {getApiError(error).message || t("history.loadError")}
        </p>
      ) : isLoading ? (
        <ListPanel>
          {Array.from({ length: 5 }).map((_, i) => (
            <HistoryRowSkeleton key={i} />
          ))}
        </ListPanel>
      ) : items.length === 0 ? (
        <p className="py-12 text-center text-sm text-text-muted">{t("history.empty")}</p>
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
                  {new Date(item.created_at).toLocaleDateString(locale === "en" ? "en-US" : "ru-RU", {
                    day: "numeric",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
              <span
                className={cn(
                  "flex shrink-0 items-center gap-1 text-sm font-semibold tabular-nums",
                  tab === "expense" ? "text-rose-400" : "text-emerald-400"
                )}
              >
                {tab === "expense" ? "−" : "+"}
                {formatGems(Math.abs(item.amount))}
              </span>
            </motion.div>
          ))}
        </ListPanel>
      )}
    </div>
  );
}

function FinanceStatCell({
  label,
  gems,
  credits,
  negative,
}: {
  label: string;
  gems: number;
  credits: number;
  negative?: boolean;
}) {
  const prefix = negative ? "−" : "+";
  return (
    <div>
      <p className="mb-1.5 text-[10px] font-medium uppercase tracking-wide text-text-muted">
        {label}
      </p>
      <div className="flex flex-col gap-1 text-sm font-semibold">
        <span className={cn("inline-flex items-center gap-1", negative ? "text-rose-400" : "text-emerald-400")}>
          {prefix}
          {formatGems(gems)}
          <AnimeGemIcon className="h-3.5 w-3.5" />
        </span>
        <span className={cn("inline-flex items-center gap-1", negative ? "text-rose-400" : "text-emerald-400")}>
          {prefix}
          {formatGems(credits)}
          <AnimeHeartIcon className="h-3.5 w-3.5" />
        </span>
      </div>
    </div>
  );
}
