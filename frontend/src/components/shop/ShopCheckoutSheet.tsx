"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AnimeGemIcon } from "@/components/icons/CurrencyIcons";
import { CHAT_BORDER } from "@/lib/theme";
import {
  discountedStars,
  starsPrice,
  usdFromStars,
  type ShopProduct,
} from "@/lib/shop";
import { canPayWithTelegramStars } from "@/lib/telegram-webapp";
import { cn } from "@/lib/utils";

export type ShopPaymentChoice = "stars" | "skip";

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
  const starsAvailable = canPayWithTelegramStars();
  const [choice, setChoice] = useState<ShopPaymentChoice>(starsAvailable ? "stars" : "skip");
  const [promo, setPromo] = useState("");
  const [promoDiscount, setPromoDiscount] = useState(0);
  const [promoMessage, setPromoMessage] = useState("");
  const [promoChecking, setPromoChecking] = useState(false);

  useEffect(() => {
    if (open) {
      setChoice(starsAvailable ? "stars" : "skip");
    }
  }, [open, starsAvailable]);

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
        setPromoMessage(res.message || "Неверный промокод");
      }
    } catch {
      setPromoDiscount(0);
      setPromoMessage("Не удалось проверить промокод");
    } finally {
      setPromoChecking(false);
    }
  };

  const handleClose = () => {
    setPromo("");
    setPromoDiscount(0);
    setPromoMessage("");
    setChoice(starsAvailable ? "stars" : "skip");
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

            <div
              className="mt-4 flex gap-1 rounded-2xl bg-bg-elevated/60 p-1"
              style={{ border: `1px solid ${CHAT_BORDER}` }}
            >
              <button
                type="button"
                disabled={!starsAvailable}
                onClick={() => setChoice("stars")}
                className={cn(
                  "flex-1 rounded-xl py-2.5 text-sm font-semibold transition-all disabled:opacity-40",
                  choice === "stars"
                    ? "bg-accent/25 text-accent-light"
                    : "text-text-muted"
                )}
              >
                ⭐ Звёздами
              </button>
              <button
                type="button"
                onClick={() => setChoice("skip")}
                className={cn(
                  "flex-1 rounded-xl py-2.5 text-sm font-semibold transition-all",
                  choice === "skip"
                    ? "bg-bg-elevated text-text-secondary"
                    : "text-text-muted"
                )}
              >
                Без оплаты
              </button>
            </div>

            {!starsAvailable && (
              <p className="mt-3 rounded-xl bg-amber-500/10 px-3 py-2 text-xs text-amber-200/90" style={{ border: `1px solid ${CHAT_BORDER}` }}>
                Оплата звёздами доступна только в Telegram Mini App (кнопка меню бота). В браузере можно только просмотреть товары.
              </p>
            )}

            {choice === "skip" ? (
              <div className="mt-5">
                <p className="text-sm text-text-secondary leading-relaxed">
                  Вы выбрали не оплачивать сейчас. Покупка не создаётся, списания не будет.
                </p>
                <button
                  type="button"
                  onClick={handleClose}
                  className="mt-5 w-full rounded-2xl py-4 text-base font-semibold text-text-secondary bg-bg-elevated active:scale-[0.98]"
                  style={{ border: `1px solid ${CHAT_BORDER}` }}
                >
                  Закрыть
                </button>
              </div>
            ) : (
              <>
                <p className="mt-3 text-sm text-text-secondary">
                  Списание с баланса Telegram Stars вашего аккаунта
                </p>

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
                        <AnimeGemIcon className="h-4 w-4" /> {product.gems_amount} гемов
                      </span>
                    )}
                    {product.credits_amount > 0 && (
                      <span
                        className="rounded-xl bg-bg-elevated px-3 py-1.5"
                        style={{ border: `1px solid ${CHAT_BORDER}` }}
                      >
                        ✨ {product.credits_amount} кредитов
                      </span>
                    )}
                  </div>
                )}

                <div className="mt-4">
                  <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-text-muted">
                    Промокод
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
                    background:
                      "linear-gradient(90deg, #9b8cff 0%, #b45cf0 45%, #9333ea 100%)",
                    boxShadow: "0 8px 28px rgba(160, 32, 240, 0.4)",
                  }}
                >
                  {loading ? "Загрузка…" : "Оплатить звёздами ⭐"}
                </button>
              </>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
