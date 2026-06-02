"use client";

import { motion } from "framer-motion";
import { Card } from "@/components/shared/Card";
import { Button } from "@/components/shared/Button";
import { useUserStore } from "@/store/user-store";
import { useToast } from "@/hooks/use-toast";
import { formatGems } from "@/lib/utils";

const PACKAGES = [
  { gems: 100, stars: 50, label: "Starter", popular: false },
  { gems: 500, stars: 200, label: "Popular", popular: true },
  { gems: 1500, stars: 500, label: "Premium", popular: false },
];

export default function ShopPage() {
  const { user } = useUserStore();
  const { toast } = useToast();

  const handlePurchase = (gems: number, stars: number) => {
    toast(`Purchase ${formatGems(gems)} gems for ${stars} Stars — coming soon`, "info");
  };

  return (
    <div className="px-4 pt-6 max-w-lg mx-auto space-y-6">
      <motion.header initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 className="text-xl font-bold">Shop</h1>
        <p className="text-text-secondary text-sm mt-1">
          Balance: <span className="text-accent font-semibold">💎 {formatGems(user?.gems ?? 0)}</span>
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
                    <span className="text-[10px] bg-accent/20 text-accent px-1.5 py-0.5 rounded-sm">
                      BEST VALUE
                    </span>
                  )}
                </div>
                <p className="text-accent font-bold mt-1">💎 {formatGems(pkg.gems)}</p>
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
