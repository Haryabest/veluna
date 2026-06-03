import { NextResponse } from "next/server";

/** Заглушка — бэкенд заменит на реальный эндпоинт */
export async function GET() {
  return NextResponse.json({
    gems: 120,
    credits: 25,
  });
}
