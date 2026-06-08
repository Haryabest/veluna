"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { History } from "lucide-react";
import { useNavStore } from "@/store/nav-store";
import { useUserStore } from "@/store/user-store";
import { usePaymentStore } from "@/store/payment-store";
import { balanceService, userService } from "@/services/api";
import { AnimeGemIcon, AnimeHeartIcon } from "@/components/icons/CurrencyIcons";
import { ListPanel } from "@/components/shared/ListPanel";
import { formatGems } from "@/lib/utils";
import { QUERY_KEYS } from "@/lib/constants";
import { useTelegramUser } from "@/hooks/use-telegram-user";
import { chatSeparatorVerticalStyle } from "@/lib/theme";

export function ProfileView() {
  const { user } = useUserStore();
  const openHistory = useNavStore((s) => s.openHistory);
  const { gems, credits, setBalance } = usePaymentStore();
  const { displayName: tgName, username: tgUsername, photoUrl: tgPhoto } = useTelegramUser();

  const displayName =
    tgName !== "Гость"
      ? tgName
      : user
        ? `${user.first_name ?? ""}${user.last_name ? ` ${user.last_name}` : ""}`.trim() || "Гость"
        : "Гость";
  const username = tgUsername ?? user?.username;
  const photoUrl = tgPhoto ?? user?.photo_url;

  const { data: balance } = useQuery({
    queryKey: QUERY_KEYS.balance,
    queryFn: () => balanceService.get(),
  });

  const { data: finance } = useQuery({
    queryKey: QUERY_KEYS.financeStats,
    queryFn: () => userService.getFinanceStats(),
    staleTime: 60_000,
  });

  useEffect(() => {
    if (balance) {
      setBalance(balance.gems, balance.credits);
    }
  }, [balance, setBalance]);

  const gemsDisplay = balance?.gems ?? gems;
  const creditsDisplay = balance?.credits ?? credits;

  return (
    <div className="mx-auto max-w-lg space-y-4 px-4 pt-6">
      <header className="flex items-center gap-4">
        <div className="h-16 w-16 overflow-hidden rounded-full bg-bg-elevated ring-2 ring-accent/30">
          {photoUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={photoUrl} alt="" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-2xl">👤</div>
          )}
        </div>
        <div>
          <h1 className="text-xl font-bold">{displayName || "Гость"}</h1>
          {username && <p className="text-sm text-text-muted">@{username}</p>}
        </div>
      </header>

      <ListPanel>
        <div className="grid grid-cols-2">
          <BalanceCell
            icon={<AnimeGemIcon className="h-[22px] w-[22px]" />}
            label="Гемы"
            value={formatGems(gemsDisplay)}
          />
          <div style={chatSeparatorVerticalStyle}>
            <BalanceCell
              icon={<AnimeHeartIcon className="h-[22px] w-[22px]" />}
              label="Сердца"
              value={formatGems(creditsDisplay)}
            />
          </div>
        </div>
      </ListPanel>

      {finance ? (
        <ListPanel>
          <div className="grid grid-cols-2 divide-x divide-white/5">
            <div className="px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-wide text-text-muted">Потрачено</p>
              <p className="mt-1 flex items-center gap-2 text-sm font-semibold text-rose-400">
                <span className="inline-flex items-center gap-1">
                  −{formatGems(finance.spent.gems)}
                  <AnimeGemIcon className="h-3.5 w-3.5" />
                </span>
                <span className="inline-flex items-center gap-1">
                  −{formatGems(finance.spent.credits)}
                  <AnimeHeartIcon className="h-3.5 w-3.5" />
                </span>
              </p>
            </div>
            <div className="px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-wide text-text-muted">Пополнено</p>
              <p className="mt-1 flex items-center gap-2 text-sm font-semibold text-emerald-400">
                <span className="inline-flex items-center gap-1">
                  +{formatGems(finance.deposited.gems)}
                  <AnimeGemIcon className="h-3.5 w-3.5" />
                </span>
                <span className="inline-flex items-center gap-1">
                  +{formatGems(finance.deposited.credits)}
                  <AnimeHeartIcon className="h-3.5 w-3.5" />
                </span>
              </p>
            </div>
          </div>
        </ListPanel>
      ) : null}

      <ListPanel>
        <button
          type="button"
          onClick={openHistory}
          className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-bg-elevated/60"
        >
          <History className="h-5 w-5 text-accent-light" strokeWidth={1.75} />
          <span className="text-sm font-medium">История</span>
        </button>
      </ListPanel>
    </div>
  );
}

function BalanceCell({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex flex-col gap-1.5 px-4 py-3">
      <span className="flex items-center gap-2">
        <span className="drop-shadow-[0_0_6px_rgba(199,125,255,0.5)]">{icon}</span>
        <span className="text-[10px] font-medium uppercase tracking-wide text-text-muted">
          {label}
        </span>
      </span>
      <p className="text-lg font-bold leading-tight text-text-primary">{value}</p>
    </div>
  );
}
