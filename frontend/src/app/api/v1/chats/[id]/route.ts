import { NextRequest, NextResponse } from "next/server";

type RouteContext = { params: Promise<{ id: string }> };

/** Заглушка — переименование чата */
export async function PATCH(request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  const body = await request.json().catch(() => ({}));
  const title = typeof body.title === "string" ? body.title.trim() : "";

  if (!title) {
    return NextResponse.json({ detail: "title is required" }, { status: 400 });
  }

  return NextResponse.json({ id, title, ok: true });
}

/** Заглушка — удаление чата */
export async function DELETE(_request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  return NextResponse.json({ id, deleted: true, ok: true });
}
