"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { useNavStore } from "@/store/nav-store";
import { useUserStore } from "@/store/user-store";
import { usePaymentStore } from "@/store/payment-store";
import { balanceService } from "@/services/api";
import { AnimeGemIcon, AnimeHeartIcon } from "@/components/icons/CurrencyIcons";
import { Card } from "@/components/shared/Card";
import { formatGems } from "@/lib/utils";
import { QUERY_KEYS } from "@/lib/constants";
import { useTelegramUser } from "@/hooks/use-telegram-user";

export function ProfileView() {
  const { user } = useUserStore();
  const openHistory = useNavStore((s) => s.openHistory);
  const openTopUp = useNavStore((s) => s.openTopUp);
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

  useEffect(() => {
    if (balance) {
      setBalance(balance.gems, balance.credits);
    }
  }, [balance, setBalance]);

  const gemsDisplay = balance?.gems ?? gems;
  const creditsDisplay = balance?.credits ?? credits;

  return (
    <div className="mx-auto max-w-lg space-y-5 px-4 pt-6">
      <motion.header
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-4"
      >
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
      </motion.header>

      <div className="grid grid-cols-2 gap-2">
        <BalanceCard
          icon={<AnimeGemIcon className="h-[22px] w-[22px]" />}
          label="Гемы"
          value={formatGems(gemsDisplay)}
          gradient="from-accent/20 to-accent-deep/10"
        />
        <BalanceCard
          icon={<AnimeHeartIcon className="h-[22px] w-[22px]" />}
          label="Кредиты"
          value={formatGems(creditsDisplay)}
          gradient="from-fuchsia-500/15 to-accent/10"
        />
      </div>

      <motion.button
        type="button"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        whileTap={{ scale: 0.98 }}
        onClick={openTopUp}
        className="w-full rounded-2xl py-3.5 text-sm font-bold uppercase tracking-wider text-white shadow-glow-sm"
        style={{
          background: "linear-gradient(90deg, #9b8cff 0%, #b45cf0 45%, #9333ea 100%)",
        }}
      >
        ПОПОЛНИТЬ БАЛАНС
      </motion.button>

      <nav className="space-y-2">
        <ProfileNavButton label="История" icon="📜" onClick={openHistory} />
      </nav>
    </div>
  );
}

function BalanceCard({
  icon,
  label,
  value,
  gradient,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  gradient: string;
}) {
  return (
    <Card className={`flex flex-col gap-2 bg-gradient-to-br ${gradient} !p-3`}>
      <span className="flex items-center gap-2">
        <span className="drop-shadow-[0_0_6px_rgba(199,125,255,0.5)]">{icon}</span>
        <span className="text-[10px] font-medium uppercase tracking-wide text-text-muted">
          {label}
        </span>
      </span>
      <p className="text-lg font-bold leading-tight text-text-primary">{value}</p>
    </Card>
  );
}

function ProfileNavButton({
  label,
  icon,
  onClick,
}: {
  label: string;
  icon: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="glass flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left transition-colors hover:bg-bg-elevated/50"
    >
      <span>{icon}</span>
      <span className="text-sm">{label}</span>
    </button>
  );
}
