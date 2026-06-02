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
    <div className="px-4 pt-6 max-w-lg mx-auto space-y-6">
      <motion.header
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-4"
      >
        <div className="w-16 h-16 rounded-full bg-bg-elevated overflow-hidden">
          {user.photo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={user.photo_url} alt="" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-2xl">👤</div>
          )}
        </div>
        <div>
          <h1 className="text-xl font-bold">
            {user.first_name} {user.last_name}
          </h1>
          {user.username && <p className="text-text-muted text-sm">@{user.username}</p>}
        </div>
      </motion.header>

      <Card className="flex items-center justify-between">
        <span className="text-text-secondary">Gems Balance</span>
        <span className="text-accent font-bold text-lg">💎 {formatGems(user.gems)}</span>
      </Card>

      <nav className="space-y-2">
        {[
          { href: ROUTES.settings, label: "Settings", icon: "⚙️" },
          { href: ROUTES.shop, label: "Buy Gems", icon: "💎" },
          ...(user.role === "admin" ? [{ href: ROUTES.admin, label: "Admin Panel", icon: "🔧" }] : []),
        ].map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="glass rounded-lg px-4 py-3 flex items-center gap-3 hover:bg-bg-elevated transition-colors"
          >
            <span>{item.icon}</span>
            <span className="text-sm">{item.label}</span>
          </Link>
        ))}
      </nav>
    </div>
  );
}
