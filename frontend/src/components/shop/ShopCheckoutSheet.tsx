"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AnimeGemIcon, AnimeHeartIcon } from "@/components/icons/CurrencyIcons";
import { CHAT_BORDER } from "@/lib/theme";
import {
  discountedStars,
  starsPrice,
  usdFromStars,
  type ShopProduct,
} from "@/lib/shop";
import { canPayWithTelegramStars } from "@/lib/telegram-webapp";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/hooks/use-translation";

interface ShopCheckoutSheetProps {
  product: ShopProduct | null;
  open: boolean;
  onClose: () => void;
  onPayStars: (promoCode: string) => Promise<void>;
  loading?: boolean;
}

export function ShopCheckoutSheet({
  product,
  open,
  onClose,
  onPayStars,
  loading = false,
}: ShopCheckoutSheetProps) {
  const { t } = useTranslation();
  const starsAvailable = canPayWithTelegramStars();
  const [promo, setPromo] = useState("");
  const [promoDiscount, setPromoDiscount] = useState(0);
  const [promoMessage, setPromoMessage] = useState("");
  const [promoChecking, setPromoChecking] = useState(false);

  useEffect(() => {
    if (!open) {
      setPromo("");
      setPromoDiscount(0);
      setPromoMessage("");
    }
  }, [open]);

  if (!product) return null;

  const baseStars = starsPrice(product);
  const finalStars = discountedStars(baseStars, promoDiscount);
  const finalUsd = usdFromStars(finalStars);

  const handleValidatePromo = async () => {
    if (!promo.trim()) return;
    setPromoChecking(true);
    try {
      const { shopService } = await import("@/services/api");
      const res = await shopService.validatePromo(promo.trim());
      if (res.valid) {
        setPromoDiscount(res.discount_percent);
        setPromoMessage(res.message);
      } else {
        setPromoDiscount(0);
        setPromoMessage(res.message || t("shop.checkout.invalidPromo"));
      }
    } catch {
      setPromoDiscount(0);
      setPromoMessage(t("shop.checkout.promoCheckError"));
    } finally {
      setPromoChecking(false);
    }
  };

  const handleClose = () => {
    setPromo("");
    setPromoDiscount(0);
    setPromoMessage("");
    onClose();
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/55"
            onClick={handleClose}
          />
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 320 }}
            className="fixed inset-x-0 bottom-0 z-50 mx-auto max-w-lg rounded-t-3xl bg-bg-secondary px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-3"
            style={{ borderTop: `1px solid ${CHAT_BORDER}` }}
          >
            <div className="mb-4 flex justify-center">
              <div className="h-1 w-9 rounded-full bg-accent/30" />
            </div>

            <h2 className="text-lg font-bold">{product.name}</h2>

            <p className="mt-3 text-sm text-text-secondary">
              {t("shop.checkout.starsHint")}
            </p>

            {!starsAvailable && (
              <p
                className="mt-3 rounded-xl bg-amber-500/10 px-3 py-2 text-xs text-amber-200/90"
                style={{ border: `1px solid ${CHAT_BORDER}` }}
              >
                {t("shop.checkout.miniAppOnly")}
              </p>
            )}

            <div
              className="mt-4 flex items-end justify-between rounded-2xl bg-bg-elevated/60 p-4"
              style={{ border: `1px solid ${CHAT_BORDER}` }}
            >
              <div>
                <p className="text-2xl font-bold text-accent-light">⭐ {finalStars}</p>
                <p className="text-sm text-text-muted">≈ ${finalUsd.toFixed(2)} USD</p>
              </div>
              {promoDiscount > 0 && (
                <span className="rounded-full bg-accent/20 px-2.5 py-1 text-xs font-semibold text-accent-light">
                  −{promoDiscount}%
                </span>
              )}
            </div>

            {(product.gems_amount > 0 || product.credits_amount > 0) && (
              <div className="mt-3 flex flex-wrap gap-2 text-sm text-text-secondary">
                {product.gems_amount > 0 && (
                  <span
                    className="flex items-center gap-1 rounded-xl bg-bg-elevated px-3 py-1.5"
                    style={{ border: `1px solid ${CHAT_BORDER}` }}
                  >
                    <AnimeGemIcon className="h-4 w-4" /> {product.gems_amount} {t("common.gemsCount")}
                  </span>
                )}
                {product.credits_amount > 0 && (
                  <span
                    className="flex items-center gap-1 rounded-xl bg-bg-elevated px-3 py-1.5"
                    style={{ border: `1px solid ${CHAT_BORDER}` }}
                  >
                    <AnimeHeartIcon className="h-4 w-4" /> {product.credits_amount} {t("common.heartsCount")}
                  </span>
                )}
              </div>
            )}

            <div className="mt-4">
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-text-muted">
                {t("shop.checkout.promo")}
              </label>
              <div className="flex gap-2">
                <input
                  value={promo}
                  onChange={(e) => setPromo(e.target.value.toUpperCase())}
                  placeholder="VELUNA10"
                  className="min-w-0 flex-1 rounded-xl bg-bg-elevated px-3 py-2.5 text-sm outline-none focus:ring-0"
                  style={{ border: `1px solid ${CHAT_BORDER}` }}
                />
                <button
                  type="button"
                  onClick={handleValidatePromo}
                  disabled={promoChecking || !promo.trim()}
                  className="shrink-0 rounded-xl bg-bg-elevated px-4 py-2.5 text-sm font-medium text-accent-light disabled:opacity-50"
                  style={{ border: `1px solid ${CHAT_BORDER}` }}
                >
                  {promoChecking ? "…" : "OK"}
                </button>
              </div>
              {promoMessage && (
                <p
                  className={cn(
                    "mt-1.5 text-xs",
                    promoDiscount > 0 ? "text-emerald-400" : "text-red-400"
                  )}
                >
                  {promoMessage}
                </p>
              )}
            </div>

            <button
              type="button"
              disabled={loading || !starsAvailable}
              onClick={() => onPayStars(promo.trim())}
              className="mt-5 w-full rounded-2xl py-4 text-base font-bold uppercase tracking-wide text-text-primary transition-transform active:scale-[0.98] disabled:opacity-60"
              style={{
                background: "linear-gradient(90deg, #9b8cff 0%, #b45cf0 45%, #9333ea 100%)",
                boxShadow: "0 8px 28px rgba(160, 32, 240, 0.4)",
              }}
            >
              {loading ? t("shop.loading") : t("shop.checkout.payStars")}
            </button>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
