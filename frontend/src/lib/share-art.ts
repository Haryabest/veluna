import { generationService } from "@/services/api";
import { apiClient, ensureTelegramSession } from "@/lib/api-client";
import {
  canShareViaTelegram,
  getTelegramBotLink,
  openTelegramTextShare,
  sharePreparedTelegramMessage,
} from "@/lib/telegram-share";

async function shareImageFileWithBotLink(
  imageUrl: string,
  botLink: string
): Promise<boolean> {
  if (typeof navigator === "undefined" || typeof navigator.share !== "function") return false;
  try {
    const { data } = await apiClient.get<Blob>(imageUrl, { responseType: "blob" });
    const mime = data.type || "image/png";
    const ext = mime.includes("jpeg")
      ? "jpg"
      : mime.includes("webp")
        ? "webp"
        : "png";
    const file = new File([data], `veluna-art.${ext}`, { type: mime });
    const text = botLink || "Смотри какой арт!";
    // navigator.canShare requires navigator.share to support `files`
    if (typeof navigator.canShare === "function" && !navigator.canShare({ files: [file] })) {
      return false;
    }
    await navigator.share({ files: [file], text, title: "Veluna" });
    return true;
  } catch {
    return false;
  }
}

export async function shareArtImage(imageUrl: string, generationId?: string): Promise<boolean> {
  await ensureTelegramSession();

  // 1) Preferred: prepared photo message in Telegram (bot uploads the file
  //    via sendPhoto, Mini App attaches it to the chat picker). The text
  //    comes from the bot and already contains the bot link.
  if (generationId && canShareViaTelegram()) {
    try {
      const prepared = await generationService.prepareShare(generationId);
      const shared = await sharePreparedTelegramMessage(prepared.prepared_message_id);
      if (shared) return true;
    } catch {
      /* fallback below */
    }
  }

  const botLink = getTelegramBotLink();

  // 2) In Mini App: share the actual image file with the bot link as text
  if (canShareViaTelegram() && typeof navigator !== "undefined" && typeof navigator.share === "function") {
    const shared = await shareImageFileWithBotLink(imageUrl, botLink);
    if (shared) return true;
  }

  // 3) Fallback: open Telegram chat picker with the bot link (no MinIO URL exposed)
  if (canShareViaTelegram()) {
    openTelegramTextShare(botLink);
    return true;
  }

  // 4) Web Share API with file attachment
  if (typeof navigator !== "undefined" && typeof navigator.share === "function") {
    const shared = await shareImageFileWithBotLink(imageUrl, botLink);
    if (shared) return true;
    try {
      await navigator.share({
        title: "Veluna",
        text: botLink || "Смотри какой арт!",
      });
      return true;
    } catch {
      /* continue */
    }
  }

  // 5) Last resort: open Telegram chat picker in browser
  openTelegramTextShare(botLink);
  return true;
}
