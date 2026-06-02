"use client";

import { motion } from "framer-motion";
import { Card } from "@/components/shared/Card";
import { Button } from "@/components/shared/Button";
import { useUserStore } from "@/store/user-store";
import { useToast } from "@/hooks/use-toast";
import { formatGems } from "@/lib/utils";

const PACKAGES = [
  { gems: 100, stars: 50, label: "Стартовый", popular: false },
  { gems: 500, stars: 200, label: "Популярный", popular: true },
  { gems: 1500, stars: 500, label: "Премиум", popular: false },
];

export default function ShopPage() {
  const { user } = useUserStore();
  const { toast } = useToast();

  const handlePurchase = (gems: number, stars: number) => {
    toast(`Покупка ${formatGems(gems)} гемов за ${stars} звёзд — скоро`, "info");
  };

  return (
    <div className="mx-auto max-w-lg space-y-6 px-4 pb-28 pt-6">
      <motion.header initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 className="text-xl font-bold">Магазин</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Баланс: <span className="font-semibold text-accent">💎 {formatGems(user?.gems ?? 0)}</span>
        </p>
      </motion.header>

      <div className="space-y-3">
        {PACKAGES.map((pkg, i) => (
          <motion.div
            key={pkg.gems}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <Card glow={pkg.popular} className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold">{pkg.label}</span>
                  {pkg.popular && (
                    <span className="rounded-full bg-accent/20 px-2 py-0.5 text-[10px] text-accent-light">
                      ВЫГОДНО
                    </span>
                  )}
                </div>
                <p className="mt-1 font-bold text-accent">💎 {formatGems(pkg.gems)}</p>
              </div>
              <Button size="sm" onClick={() => handlePurchase(pkg.gems, pkg.stars)}>
                ⭐ {pkg.stars}
              </Button>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
