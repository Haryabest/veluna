"use client";

import { motion } from "framer-motion";
import { useUserStore } from "@/store/user-store";
import { Card } from "@/components/shared/Card";
import { formatGems } from "@/lib/utils";

export function ProfileView() {
  const { user } = useUserStore();

  const displayName = user ? `${user.first_name}${user.last_name ? ` ${user.last_name}` : ""}` : "Гость";
  const username = user?.username;
  const gems = user?.gems ?? 120;
  const photoUrl = user?.photo_url;

  return (
    <div className="mx-auto max-w-lg space-y-6 px-4 pt-6">
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
          <h1 className="text-xl font-bold">{displayName}</h1>
          {username && <p className="text-sm text-text-muted">@{username}</p>}
        </div>
      </motion.header>

      <Card className="flex items-center justify-between">
        <span className="text-text-secondary">Баланс гемов</span>
        <span className="text-lg font-bold text-accent">💎 {formatGems(gems)}</span>
      </Card>

      <nav className="space-y-2">
        {[
          { label: "Настройки", icon: "⚙️" },
          { label: "Купить гемы", icon: "💎" },
        ].map((item) => (
          <button
            key={item.label}
            type="button"
            className="glass flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left transition-colors hover:bg-bg-elevated/50"
          >
            <span>{item.icon}</span>
            <span className="text-sm">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
