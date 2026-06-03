"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2 } from "lucide-react";
import { useNavStore } from "@/store/nav-store";
import { BackButton } from "@/components/shared/BackButton";
import { ListPanel } from "@/components/shared/ListPanel";
import { Separator } from "@/components/shared/Separator";
import { AnimeGemIcon, AnimeHeartIcon } from "@/components/icons/CurrencyIcons";
import { balanceService, type TopUpCurrency, type TopUpQuote } from "@/services/api";
import { CHAT_BORDER, chatSeparatorVerticalStyle } from "@/lib/theme";
import { cn, formatGems } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import { openTelegramInvoice } from "@/hooks/use-telegram-payment";
import { canPayWithTelegramStars } from "@/lib/telegram-webapp";

const PRESET_AMOUNTS = [50, 100, 250, 500];

const PANEL_GRADIENT =
  "bg-gradient-to-br from-[#2e1d48] via-[#221833] to-[#1a1228] shadow-[inset_0_1px_0_rgba(199,125,255,0.12)]";
const PANEL_ACTIVE =
  "bg-gradient-to-br from-[#6b21a8] via-[#5b21a8] to-[#3d2660] shadow-[0_0_20px_rgba(160,32,240,0.35)]";
const PANEL_INACTIVE =
  "bg-gradient-to-br from-[#2a1f3d] to-[#1e152c]";
const CTA_GRADIENT = "linear-gradient(90deg, #9b8cff 0%, #b45cf0 45%, #9333ea 100%)";

export function TopUpBalanceView() {
  const goBack = useNavStore((s) => s.goBack);
  const { toast } = useToast();
  const starsAvailable = canPayWithTelegramStars();

  const [step, setStep] = useState<1 | 2>(1);
  const [currency, setCurrency] = useState<TopUpCurrency>("gems");
  const [amount, setAmount] = useState(100);
  const [promo, setPromo] = useState("");
  const [appliedPromo, setAppliedPromo] = useState<string | null>(null);
  const [promoDiscount, setPromoDiscount] = useState(0);
  const [promoError, setPromoError] = useState("");
  const [promoApplying, setPromoApplying] = useState(false);
  const [quote, setQuote] = useState<TopUpQuote | null>(null);
  const [loading, setLoading] = useState(false);
  const [paying, setPaying] = useState(false);

  const currencyLabel = currency === "gems" ? "гемов" : "сердец";
  const promoApplied = appliedPromo !== null && promoDiscount > 0;

  const handleApplyPromo = async () => {
    const code = promo.trim();
    if (!code) {
      toast("Введите промокод", "warning");
      return;
    }
    setPromoApplying(true);
    setPromoError("");
    try {
      const res = await balanceService.getTopUpQuote({
        currency_type: currency,
        amount: Math.max(amount, 1),
        promo_code: code,
      });
      if (res.promo_valid && res.discount_percent > 0) {
        setAppliedPromo(code.toUpperCase());
        setPromoDiscount(res.discount_percent);
        setPromoError("");
        toast(`Промокод применён: скидка ${res.discount_percent}%`, "success");
      } else {
        setAppliedPromo(null);
        setPromoDiscount(0);
        setPromoError("Промокод не найден или недействителен");
        toast("Промокод не найден", "error");
      }
    } catch {
      setPromoError("Не удалось проверить промокод");
      toast("Не удалось проверить промокод", "error");
    } finally {
      setPromoApplying(false);
    }
  };

  const clearPromo = () => {
    setAppliedPromo(null);
    setPromoDiscount(0);
    setPromoError("");
  };

  const handleNext = async () => {
    if (amount < 1) {
      toast("Укажите количество", "warning");
      return;
    }
    setLoading(true);
    try {
      const res = await balanceService.getTopUpQuote({
        currency_type: currency,
        amount,
        promo_code: (appliedPromo ?? promo.trim()) || undefined,
      });
      setQuote(res);
      setStep(2);
    } catch {
      toast("Не удалось рассчитать сумму", "error");
    } finally {
      setLoading(false);
    }
  };

  const handlePay = async () => {
    if (!quote) return;

    if (!canPayWithTelegramStars()) {
      toast("Откройте пополнение через Telegram Mini App", "info");
      return;
    }

    setPaying(true);
    try {
      const res = await balanceService.topUpCheckout({
        currency_type: currency,
        amount,
        promo_code: (appliedPromo ?? promo.trim()) || undefined,
        stars_amount: quote.stars_amount,
      });

      if (res.invoice_url) {
        const status = await openTelegramInvoice(res.invoice_url);
        if (status === "paid") {
          toast("Оплата прошла! Баланс обновится в профиле", "success");
          goBack();
        } else if (status === "cancelled") {
          toast("Оплата отменена", "info");
        } else {
          toast("Не удалось завершить оплату Stars", "error");
        }
      } else {
        toast(`Заглушка: ${quote.stars_amount} ⭐ за ${amount} ${currencyLabel}`, "info");
        goBack();
      }
    } catch {
      toast("Не удалось оформить оплату", "error");
    } finally {
      setPaying(false);
    }
  };

  return (
    <div className="mx-auto max-w-lg px-4 pb-8 pt-5">
      <div className="mb-4 flex items-center gap-2">
        <BackButton onClick={step === 2 ? () => setStep(1) : goBack} />
        <div className="min-w-0 flex-1">
          <h1 className="text-xl font-bold">Пополнение</h1>
          <p className="text-xs text-text-muted">Шаг {step} из 2</p>
        </div>
      </div>

      <div
        className={cn("mb-5 flex gap-1 rounded-2xl p-1", PANEL_GRADIENT)}
        style={{ border: `1px solid ${CHAT_BORDER}` }}
      >
        {[1, 2].map((s) => (
          <div
            key={s}
            className={cn(
              "flex-1 rounded-xl py-2.5 text-center text-xs font-semibold transition-all",
              step === s ? cn(PANEL_ACTIVE, "text-white") : cn(PANEL_INACTIVE, "text-text-muted")
            )}
            style={step === s ? { border: `1px solid rgba(199, 125, 255, 0.45)` } : undefined}
          >
            {s === 1 ? "Сумма" : "Оплата"}
          </div>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {step === 1 ? (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -16 }}
            className="space-y-4"
          >
            <ListPanel>
              <div className="grid grid-cols-2">
                <CurrencyOption
                  active={currency === "gems"}
                  onClick={() => setCurrency("gems")}
                  icon={<AnimeGemIcon className="h-6 w-6" />}
                  label="Гемы"
                />
                <div style={chatSeparatorVerticalStyle}>
                  <CurrencyOption
                    active={currency === "credits"}
                    onClick={() => setCurrency("credits")}
                    icon={<AnimeHeartIcon className="h-6 w-6" />}
                    label="Сердца"
                  />
                </div>
              </div>
              <Separator />
              <div className="p-4">
              <p className="mb-3 text-sm font-semibold text-text-primary">Количество</p>
              <div className="flex items-center gap-3">
                <StepperButton label="−" onClick={() => setAmount((a) => Math.max(1, a - 10))} />
                <input
                  type="number"
                  min={1}
                  max={10000}
                  value={amount}
                  onChange={(e) => setAmount(Math.max(1, Number(e.target.value) || 1))}
                  className={cn(
                    "w-full rounded-xl px-3 py-2.5 text-center text-lg font-bold text-text-primary outline-none",
                    PANEL_INACTIVE
                  )}
                  style={{ border: `1px solid ${CHAT_BORDER}` }}
                />
                <StepperButton label="+" onClick={() => setAmount((a) => Math.min(10000, a + 10))} />
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {PRESET_AMOUNTS.map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setAmount(n)}
                    className={cn(
                      "rounded-full px-3 py-1.5 text-xs font-semibold transition-all",
                      amount === n
                        ? cn(PANEL_ACTIVE, "text-white")
                        : cn(PANEL_INACTIVE, "text-text-muted hover:text-text-secondary")
                    )}
                    style={{ border: `1px solid ${CHAT_BORDER}` }}
                  >
                    {n}
                  </button>
                ))}
              </div>
              </div>
              <Separator />
              <div className="p-4">
              <p className="mb-3 text-sm font-semibold text-text-primary">Промокод</p>
              <div className="flex gap-2">
                <input
                  value={promo}
                  onChange={(e) => {
                    setPromo(e.target.value.toUpperCase());
                    if (appliedPromo && e.target.value.toUpperCase() !== appliedPromo) {
                      clearPromo();
                    }
                  }}
                  placeholder="VELUNA10"
                  className={cn(
                    "min-w-0 flex-1 rounded-xl px-3 py-2.5 text-sm text-text-primary outline-none placeholder:text-text-muted",
                    PANEL_INACTIVE
                  )}
                  style={{ border: `1px solid ${CHAT_BORDER}` }}
                />
                <button
                  type="button"
                  disabled={promoApplying || !promo.trim()}
                  onClick={handleApplyPromo}
                  className={cn(
                    "shrink-0 rounded-xl px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50",
                    PANEL_ACTIVE
                  )}
                  style={{ border: `1px solid rgba(199, 125, 255, 0.5)` }}
                >
                  {promoApplying ? "…" : "Применить"}
                </button>
              </div>

              <AnimatePresence>
                {promoApplied && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-3 flex items-start gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-emerald-900/50 via-emerald-800/40 to-teal-900/30 px-3 py-2.5"
                    style={{ border: "1px solid rgba(52, 211, 153, 0.45)" }}
                    role="alert"
                  >
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                    <div className="min-w-0 text-xs">
                      <p className="font-semibold text-emerald-300">Промокод применён</p>
                      <p className="text-emerald-200/90">
                        {appliedPromo} — скидка {promoDiscount}%
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {promoError && !promoApplied && (
                <p className="mt-2 text-xs text-amber-300" role="alert">
                  {promoError}
                </p>
              )}
              </div>
            </ListPanel>

            <button
              type="button"
              disabled={loading}
              onClick={handleNext}
              className="w-full rounded-2xl py-4 text-sm font-bold uppercase tracking-wide text-white shadow-glow-sm disabled:opacity-50"
              style={{ background: CTA_GRADIENT }}
            >
              {loading ? "Считаем…" : "Далее"}
            </button>
          </motion.div>
        ) : (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -16 }}
            className="space-y-4"
          >
            {quote && (
              <ListPanel className="space-y-0 p-4 text-sm">
                <SummaryRow
                  label="Получите"
                  value={`${formatGems(amount)} ${currency === "gems" ? "гемов" : "сердец"}`}
                />
                {(quote.discount_percent > 0 || appliedPromo) && <Separator className="my-3" />}
                {quote.discount_percent > 0 && (
                  <SummaryRow label="Скидка" value={`${quote.discount_percent}%`} accent />
                )}
                {appliedPromo && (
                  <SummaryRow label="Промокод" value={appliedPromo} accent />
                )}
                <Separator className="my-3" />
                <SummaryRow label="К оплате" value={`⭐ ${quote.stars_amount}`} bold />
                <SummaryRow label="≈ USD" value={`$${quote.usd_amount.toFixed(2)}`} muted />
              </ListPanel>
            )}

            {!starsAvailable && (
              <p
                className="rounded-xl bg-amber-500/10 px-3 py-2.5 text-xs text-amber-200/90"
                style={{ border: `1px solid ${CHAT_BORDER}` }}
              >
                Оплата Telegram Stars доступна только в Mini App (кнопка бота в Telegram).
              </p>
            )}

            <p className="text-sm text-text-secondary">
              Списание с баланса Telegram Stars вашего аккаунта
            </p>

            <button
              type="button"
              disabled={paying || !starsAvailable}
              onClick={handlePay}
              className="w-full rounded-2xl py-4 text-sm font-bold uppercase tracking-wide text-white shadow-glow-sm disabled:opacity-50"
              style={{ background: CTA_GRADIENT }}
            >
              {paying ? "Обработка…" : `Оплатить ⭐ ${quote?.stars_amount ?? 0}`}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function CurrencyOption({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex w-full flex-col items-center gap-2 px-3 py-4 transition-all",
        active ? cn(PANEL_ACTIVE, "text-white") : "text-text-muted hover:bg-bg-elevated/40"
      )}
    >
      {icon}
      <span className="text-sm font-semibold">{label}</span>
    </button>
  );
}

function StepperButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-lg font-bold text-text-primary active:scale-95",
        PANEL_INACTIVE
      )}
      style={{ border: `1px solid ${CHAT_BORDER}` }}
    >
      {label}
    </button>
  );
}

function SummaryRow({
  label,
  value,
  bold,
  accent,
  muted,
}: {
  label: string;
  value: string;
  bold?: boolean;
  accent?: boolean;
  muted?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className={muted ? "text-text-muted" : "text-text-secondary"}>{label}</span>
      <span
        className={cn(
          bold && "text-base font-bold text-accent-light",
          accent && "text-emerald-400",
          !bold && !accent && !muted && "font-medium text-text-primary",
          muted && "text-text-muted"
        )}
      >
        {value}
      </span>
    </div>
  );
}
