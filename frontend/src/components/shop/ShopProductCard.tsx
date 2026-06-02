"use client";

import { motion } from "framer-motion";
import { AnimeGemIcon } from "@/components/icons/CurrencyIcons";
import { CHAT_BORDER } from "@/lib/theme";
import { starsPrice, usdFromStars, type ShopProduct } from "@/lib/shop";
import { cn } from "@/lib/utils";

const TYPE_STYLES: Record<
  ShopProduct["product_type"],
  { gradient: string; icon: string; label: string }
> = {
  bundle: {
    gradient: "from-violet-600/40 via-fuchsia-600/20 to-bg-elevated",
    icon: "🎁",
    label: "Набор",
  },
  gems: {
    gradient: "from-purple-600/35 via-indigo-600/15 to-bg-elevated",
    icon: "💎",
    label: "Гемы",
  },
  credits: {
    gradient: "from-pink-600/30 via-purple-600/15 to-bg-elevated",
    icon: "✨",
    label: "Кредиты",
  },
};

interface ShopProductCardProps {
  product: ShopProduct;
  index?: number;
  onSelect: () => void;
}

export function ShopProductCard({ product, index = 0, onSelect }: ShopProductCardProps) {
  const style = TYPE_STYLES[product.product_type];
  const stars = starsPrice(product);
  const usd = usdFromStars(stars);
  const hasSale = product.sale_price != null && product.sale_price < product.price;

  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      onClick={onSelect}
      className={cn(
        "group w-full overflow-hidden rounded-2xl text-left transition-transform active:scale-[0.98]",
        "hover:shadow-glow"
      )}
      style={{ border: `1px solid ${CHAT_BORDER}` }}
    >
      <div className={cn("relative flex aspect-[4/3] flex-col justify-between bg-gradient-to-br p-4", style.gradient)}>
        {hasSale && (
          <span className="absolute right-3 top-3 rounded-full bg-accent px-2.5 py-0.5 text-[10px] font-bold uppercase text-text-primary">
            Sale
          </span>
        )}
        <span className="text-3xl">{style.icon}</span>
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-text-muted">{style.label}</p>
          <h3 className="mt-0.5 text-lg font-bold leading-tight">{product.name}</h3>
        </div>
      </div>

      <div className="flex items-center justify-between bg-bg-elevated/80 px-4 py-3">
        <div className="flex flex-wrap gap-2 text-xs text-text-secondary">
          {product.gems_amount > 0 && (
            <span className="flex items-center gap-1">
              <AnimeGemIcon className="h-3.5 w-3.5" />
              {product.gems_amount}
            </span>
          )}
          {product.credits_amount > 0 && <span>✨ {product.credits_amount}</span>}
        </div>
        <div className="text-right">
          <p className="font-bold text-accent-light">
            ⭐ {stars}
            {hasSale && (
              <span className="ml-1.5 text-xs font-normal text-text-muted line-through">
                {product.price}
              </span>
            )}
          </p>
          <p className="text-[11px] text-text-muted">${usd.toFixed(2)}</p>
        </div>
      </div>
    </motion.button>
  );
}
