"use client";

import { motion } from "framer-motion";
import { AnimeGemIcon, AnimeHeartIcon } from "@/components/icons/CurrencyIcons";
import { chatBorderStyle, chatSeparatorStyle } from "@/lib/theme";
import { starsPrice, usdFromStars, type ShopProduct } from "@/lib/shop";
import { cn } from "@/lib/utils";

const TYPE_META: Record<
  ShopProduct["product_type"],
  { emoji: string; label: string }
> = {
  bundle: { emoji: "🎁", label: "Набор" },
  gems: { emoji: "💎", label: "Гемы" },
  credits: { emoji: "✨", label: "Кредиты" },
};

interface ShopProductCardProps {
  product: ShopProduct;
  index?: number;
  showSeparator?: boolean;
  onSelect: () => void;
}

export function ShopProductCard({
  product,
  index = 0,
  showSeparator = true,
  onSelect,
}: ShopProductCardProps) {
  const meta = TYPE_META[product.product_type];
  const stars = starsPrice(product);
  const usd = usdFromStars(stars);
  const hasSale = product.sale_price != null && product.sale_price < product.price;

  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      onClick={onSelect}
      className={cn(
        "flex w-full items-center gap-3 px-4 py-3 text-left transition-colors",
        "hover:bg-bg-elevated/60 active:bg-bg-elevated/80"
      )}
      style={showSeparator ? chatSeparatorStyle : undefined}
    >
      <span
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-bg-elevated text-lg"
        style={chatBorderStyle}
      >
        {meta.emoji}
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-sm font-semibold text-text-primary">{product.name}</p>
          {hasSale && (
            <span className="shrink-0 rounded bg-accent/30 px-1.5 py-0.5 text-[9px] font-bold uppercase text-accent-light">
              Sale
            </span>
          )}
        </div>
        <p className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-text-muted">
          <span>{meta.label}</span>
          {product.gems_amount > 0 && (
            <span className="inline-flex items-center gap-0.5">
              <AnimeGemIcon className="h-3 w-3" />
              {product.gems_amount}
            </span>
          )}
          {product.credits_amount > 0 && (
            <span className="inline-flex items-center gap-0.5">
              <AnimeHeartIcon className="h-3 w-3" />
              {product.credits_amount}
            </span>
          )}
        </p>
      </div>

      <div className="shrink-0 text-right">
        <p className="text-sm font-bold leading-tight text-accent-light">
          ⭐ {stars}
          {hasSale && (
            <span className="ml-1 text-[10px] font-normal text-text-muted line-through">
              {product.price}
            </span>
          )}
        </p>
        <p className="text-[10px] text-text-muted">${usd.toFixed(2)}</p>
      </div>
    </motion.button>
  );
}
