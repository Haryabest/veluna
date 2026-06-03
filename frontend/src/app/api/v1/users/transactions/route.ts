import { NextRequest, NextResponse } from "next/server";

const EXPENSES = [
  {
    id: "exp-1",
    amount: -15,
    currency: "gems" as const,
    description: "Сообщение в чате — Акира",
    created_at: "2026-06-02T14:30:00Z",
  },
  {
    id: "exp-2",
    amount: -3,
    currency: "credits" as const,
    description: "Генерация изображения",
    created_at: "2026-06-01T09:15:00Z",
  },
  {
    id: "exp-3",
    amount: -50,
    currency: "gems" as const,
    description: "Разблокировка сценария",
    created_at: "2026-05-28T18:00:00Z",
  },
];

const DEPOSITS = [
  {
    id: "dep-1",
    amount: 500,
    currency: "gems" as const,
    description: "Покупка в магазине — Стартовый набор",
    created_at: "2026-06-01T12:00:00Z",
  },
  {
    id: "dep-2",
    amount: 50,
    currency: "credits" as const,
    description: "Покупка кредитов",
    created_at: "2026-05-30T10:20:00Z",
  },
  {
    id: "dep-3",
    amount: 100,
    currency: "gems" as const,
    description: "Ежедневный бонус",
    created_at: "2026-05-29T08:00:00Z",
  },
];

/** Заглушка — бэкенд заменит на реальный эндпоинт */
export async function GET(request: NextRequest) {
  const type = request.nextUrl.searchParams.get("type");
  const items = type === "deposit" ? DEPOSITS : EXPENSES;

  return NextResponse.json({ items, type: type === "deposit" ? "deposit" : "expense" });
}
