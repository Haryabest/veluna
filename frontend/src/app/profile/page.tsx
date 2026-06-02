"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useUserStore } from "@/store/user-store";
import { Card } from "@/components/shared/Card";
import { ROUTES } from "@/lib/constants";
import { formatGems } from "@/lib/utils";

export default function ProfilePage() {
  const { user } = useUserStore();

  if (!user) return null;

  return (
    <div className="mx-auto max-w-lg space-y-6 px-4 pb-28 pt-6">
      <motion.header
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-4"
      >
        <div className="h-16 w-16 overflow-hidden rounded-full bg-bg-elevated">
          {user.photo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={user.photo_url} alt="" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-2xl">👤</div>
          )}
        </div>
        <div>
          <h1 className="text-xl font-bold">
            {user.first_name} {user.last_name}
          </h1>
          {user.username && <p className="text-sm text-text-muted">@{user.username}</p>}
        </div>
      </motion.header>

      <Card className="flex items-center justify-between">
        <span className="text-text-secondary">Баланс гемов</span>
        <span className="text-lg font-bold text-accent">💎 {formatGems(user.gems)}</span>
      </Card>

      <nav className="space-y-2">
        {[
          { href: ROUTES.settings, label: "Настройки", icon: "⚙️" },
          { href: ROUTES.shop, label: "Купить гемы", icon: "💎" },
          ...(user.role === "admin" ? [{ href: ROUTES.admin, label: "Админ-панель", icon: "🔧" }] : []),
        ].map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="glass flex items-center gap-3 rounded-2xl px-4 py-3 transition-colors hover:bg-bg-elevated/50"
          >
            <span>{item.icon}</span>
            <span className="text-sm">{item.label}</span>
          </Link>
        ))}
      </nav>
    </div>
  );
}
