import { API_URL } from "./constants";
import { isTelegramWebApp } from "./telegram-webapp";

export const PROFILE_AVATAR_PROXY = `${API_URL}/users/me/avatar`;

export function isProfileAvatarProxy(url?: string | null): boolean {
  if (!url) return false;
  return url.includes("/users/me/avatar");
}

export function isTelegramPhotoUrl(url?: string | null): boolean {
  if (!url) return false;
  return /t\.me\/i\/userpic|telegram\.(org|me)|api\.telegram\.org\/file\//i.test(url);
}

/** Same-origin proxy in Mini App — avoids iOS WebView opening t.me in Safari. */
export function resolveProfileAvatarUrl(
  tgPhoto: string | null | undefined,
  ...candidates: Array<string | null | undefined>
): string | null {
  if (isTelegramWebApp()) {
    return PROFILE_AVATAR_PROXY;
  }
  for (const url of [tgPhoto, ...candidates]) {
    if (!url) continue;
    if (url.includes("/media/previews/avatars/") || url.includes("/media/users/")) continue;
    return url;
  }
  return null;
}
