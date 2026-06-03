import { NextRequest, NextResponse } from "next/server";

const PROMOS: Record<string, number> = {
  VELUNA10: 10,
  WELCOME: 15,
};

/** Заглушка — расчёт суммы пополнения */
export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const currencyType = body.currency_type === "credits" ? "credits" : "gems";
  const amount = Math.max(1, Math.min(10000, Number(body.amount) || 0));
  const promoCode = typeof body.promo_code === "string" ? body.promo_code.trim().toUpperCase() : "";

  const discountPercent = promoCode ? (PROMOS[promoCode] ?? 0) : 0;
  const unitStars = currencyType === "gems" ? 1 : 2;
  const subtotalStars = amount * unitStars;
  const starsAmount = Math.max(1, Math.ceil(subtotalStars * (1 - discountPercent / 100)));

  return NextResponse.json({
    currency_type: currencyType,
    amount,
    promo_code: promoCode || null,
    discount_percent: discountPercent,
    promo_valid: !promoCode || discountPercent > 0,
    promo_message:
      promoCode && discountPercent === 0
        ? "Промокод не найден"
        : promoCode
          ? `Скидка ${discountPercent}%`
          : null,
    stars_amount: starsAmount,
    usd_amount: Number((starsAmount * 0.013).toFixed(2)),
    ok: true,
  });
}
