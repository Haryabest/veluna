/** Relative /api/v1 uses Next.js dev proxy or nginx in production. Set NEXT_PUBLIC_API_URL for tunnel deploys. */
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ||
  (typeof window !== "undefined"
    ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws`
    : "ws://127.0.0.1:8000/ws");
export const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "Veluna";

export const ROUTES = {
  home: "/",
  character: (id: string) => `/characters/${id}`,
  chat: (id: string) => `/chat/${id}`,
  generate: "/generate",
  shop: "/shop",
  profile: "/profile",
  settings: "/settings",
  admin: "/admin",
} as const;

export const QUERY_KEYS = {
  user: ["user"] as const,
  characters: ["characters"] as const,
  character: (id: string) => ["character", id] as const,
  chats: ["chats"] as const,
  chat: (id: string) => ["chat", id] as const,
  messages: (chatId: string) => ["messages", chatId] as const,
  generations: ["generations"] as const,
  balance: ["balance"] as const,
  transactions: ["transactions"] as const,
  adminStats: ["admin", "stats"] as const,
} as const;
