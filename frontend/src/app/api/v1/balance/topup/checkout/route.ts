import { NextRequest, NextResponse } from "next/server";

/** Заглушка — оформление пополнения через Telegram Stars */
export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const currencyType = body.currency_type === "credits" ? "credits" : "gems";
  const amount = Number(body.amount) || 0;

  return NextResponse.json({
    purchase_id: `topup-stub-${Date.now()}`,
    invoice_url: "",
    currency_type: currencyType,
    amount,
    payment_method: "stars",
    stars_amount: Number(body.stars_amount) || 0,
    status: "pending",
    ok: true,
  });
}
