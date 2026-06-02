"use client";

import { motion } from "framer-motion";
import { useNavStore } from "@/store/nav-store";
import { useUserStore } from "@/store/user-store";
import { AnimeGemIcon, AnimeHeartIcon } from "@/components/icons/CurrencyIcons";
import { formatGems } from "@/lib/utils";

interface CurrencyBarProps {
  hearts?: number;
}

export function CurrencyBar({ hearts = 25 }: CurrencyBarProps) {
  const { user } = useUserStore();
  const openShop = useNavStore((s) => s.openShop);
  const gems = user?.gems ?? 120;

  return (
    <motion.header
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-2"
    >
      <div className="flex min-w-0 flex-1 gap-2">
        <CurrencyPill
          icon={<AnimeGemIcon className="h-[22px] w-[22px]" />}
          value={formatGems(gems)}
          label="Гемы"
          gradient="from-accent/20 to-accent-deep/10"
        />
        <CurrencyPill
          icon={<AnimeHeartIcon className="h-[22px] w-[22px]" />}
          value={formatGems(hearts)}
          label="Сердца"
          gradient="from-fuchsia-500/15 to-accent/10"
        />
      </div>

      <motion.button
        type="button"
        whileTap={{ scale: 0.92 }}
        onClick={openShop}
        aria-label="Магазин"
        className="glass-strong flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-accent/20 bg-gradient-to-br from-accent/25 to-accent-deep/20 shadow-glow-sm"
      >
        <MarketIcon />
      </motion.button>
    </motion.header>
  );
}

function CurrencyPill({
  icon,
  value,
  label,
  gradient,
}: {
  icon: React.ReactNode;
  value: string;
  label: string;
  gradient: string;
}) {
  return (
    <div
      className={`glass flex min-w-0 flex-1 items-center gap-2.5 rounded-2xl bg-gradient-to-r ${gradient} px-3 py-2.5`}
    >
      <span className="flex shrink-0 items-center justify-center drop-shadow-[0_0_6px_rgba(199,125,255,0.5)]">
        {icon}
      </span>
      <div className="min-w-0">
        <p className="truncate text-sm font-semibold leading-tight text-text-primary">{value}</p>
        <p className="text-[10px] font-medium uppercase tracking-wide text-text-muted">{label}</p>
      </div>
    </div>
  );
}

function MarketIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="text-accent-light" aria-hidden>
      <path
        d="M6 6h15l-1.5 9h-12L6 6z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M6 6L5 3H2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="9" cy="20" r="1.5" fill="currentColor" />
      <circle cx="18" cy="20" r="1.5" fill="currentColor" />
    </svg>
  );
}
