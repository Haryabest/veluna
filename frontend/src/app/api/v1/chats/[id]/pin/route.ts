import { NextRequest, NextResponse } from "next/server";

type RouteContext = { params: Promise<{ id: string }> };

/** Заглушка — закрепление чата */
export async function PATCH(request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  const body = await request.json().catch(() => ({}));
  const pinned = Boolean(body.pinned);

  return NextResponse.json({ id, pinned, ok: true });
}
