"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useUserStore } from "@/store/user-store";
import { ROUTES } from "@/lib/constants";
import { formatGems } from "@/lib/utils";

interface CurrencyBarProps {
  stars?: number;
}

export function CurrencyBar({ stars = 0 }: CurrencyBarProps) {
  const { user } = useUserStore();
  const gems = user?.gems ?? 120;

  return (
    <motion.header
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-2.5"
    >
      <div className="flex flex-1 gap-2 min-w-0">
        <CurrencyPill
          icon={<GemIcon />}
          value={formatGems(gems)}
          label="Гемы"
          gradient="from-accent/20 to-accent-deep/10"
        />
        <CurrencyPill
          icon={<StarIcon />}
          value={formatGems(stars)}
          label="Звёзды"
          gradient="from-accent-light/15 to-accent/10"
        />
      </div>

      <Link href={ROUTES.shop} aria-label="Магазин">
        <motion.div
          whileTap={{ scale: 0.92 }}
          className="glass-strong flex h-11 w-11 shrink-0 items-center justify-center rounded-full border-accent/20 bg-gradient-to-br from-accent/25 to-accent-deep/20 shadow-glow-sm"
        >
          <MarketIcon />
        </motion.div>
      </Link>
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
      className={`glass flex flex-1 min-w-0 items-center gap-2 rounded-2xl bg-gradient-to-r ${gradient} px-3 py-2.5`}
    >
      <span className="shrink-0 text-accent-light">{icon}</span>
      <div className="min-w-0">
        <p className="truncate text-sm font-semibold leading-tight text-text-primary">{value}</p>
        <p className="text-[10px] font-medium uppercase tracking-wide text-text-muted">{label}</p>
      </div>
    </div>
  );
}

function GemIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M12 2L2 9l10 13L22 9 12 2z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M2 9h20" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

function StarIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6L12 2z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function MarketIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M6 6h15l-1.5 9h-12L6 6z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path
        d="M6 6L5 3H2"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <circle cx="9" cy="20" r="1.5" fill="currentColor" />
      <circle cx="18" cy="20" r="1.5" fill="currentColor" />
    </svg>
  );
}
