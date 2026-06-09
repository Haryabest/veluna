import { API_URL } from "./constants";
import { isTelegramWebApp } from "./telegram-webapp";

/** Same-origin avatar URL for <img src> (works in Telegram iOS WebView). */
export function resolveProfileAvatarUrl(
  tgPhoto: string | null | undefined,
  ...candidates: Array<string | null | undefined>
): string | null {
  if (typeof window !== "undefined" && isTelegramWebApp()) {
    const token = localStorage.getItem("access_token");
    const base = `${API_URL}/users/me/avatar`;
    return token ? `${base}?access_token=${encodeURIComponent(token)}` : base;
  }

  for (const url of [tgPhoto, ...candidates]) {
    if (!url) continue;
    if (url.includes("/media/previews/avatars/") || url.includes("/media/users/")) continue;
    return url;
  }
  return null;
}
