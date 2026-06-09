function startOfLocalDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

export function parseMessageDate(iso?: string): Date | null {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

export function getDayKey(iso?: string): string | null {
  const d = parseMessageDate(iso);
  if (!d) return null;
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function shouldShowDaySeparator(
  prev: { created_at?: string } | undefined,
  curr: { created_at?: string }
): boolean {
  const currKey = getDayKey(curr.created_at);
  if (!currKey) return false;
  if (!prev) return true;
  const prevKey = getDayKey(prev.created_at);
  if (!prevKey) return true;
  return currKey !== prevKey;
}

/** Telegram-style day label: Сегодня / Вчера / weekday / date */
export function formatChatDayLabel(iso: string): string {
  const d = parseMessageDate(iso);
  if (!d) return "";
  const now = new Date();
  const diffDays = Math.round(
    (startOfLocalDay(now).getTime() - startOfLocalDay(d).getTime()) / 86400000
  );

  if (diffDays === 0) return "Сегодня";
  if (diffDays === 1) return "Вчера";

  if (diffDays >= 2 && diffDays < 7) {
    const weekday = d.toLocaleDateString("ru-RU", { weekday: "long" });
    return weekday.charAt(0).toUpperCase() + weekday.slice(1);
  }

  if (d.getFullYear() === now.getFullYear()) {
    return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
  }

  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });
}

export type ChatDayRow = { kind: "day"; id: string; label: string };
export type ChatMessageRow<T> = { kind: "message"; id: string; msg: T };
export type ChatRow<T> = ChatDayRow | ChatMessageRow<T>;

export function buildChatMessageRows<T extends { id: string; created_at?: string }>(
  messages: T[]
): ChatRow<T>[] {
  const rows: ChatRow<T>[] = [];
  for (let i = 0; i < messages.length; i++) {
    const msg = messages[i];
    const prev = messages[i - 1];
    if (shouldShowDaySeparator(prev, msg) && msg.created_at) {
      rows.push({
        kind: "day",
        id: `day-${getDayKey(msg.created_at)}-${i}`,
        label: formatChatDayLabel(msg.created_at),
      });
    }
    rows.push({ kind: "message", id: msg.id, msg });
  }
  return rows;
}
