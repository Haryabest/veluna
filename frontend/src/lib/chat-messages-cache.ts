const PREFIX = "veluna_msgs_";
const TTL_MS = 30 * 60 * 1000;

type CachedMessages = {
  savedAt: number;
  messages: unknown[];
};

export function readMessagesCache(chatId: string): unknown[] | undefined {
  if (typeof window === "undefined" || !chatId) return undefined;
  try {
    const raw = localStorage.getItem(`${PREFIX}${chatId}`);
    if (!raw) return undefined;
    const parsed = JSON.parse(raw) as CachedMessages;
    if (Date.now() - parsed.savedAt > TTL_MS) return undefined;
    return parsed.messages;
  } catch {
    return undefined;
  }
}

export function writeMessagesCache(chatId: string, messages: unknown[]) {
  if (typeof window === "undefined" || !chatId) return;
  try {
    const payload: CachedMessages = { savedAt: Date.now(), messages };
    localStorage.setItem(`${PREFIX}${chatId}`, JSON.stringify(payload));
  } catch {
    /* ignore */
  }
}
