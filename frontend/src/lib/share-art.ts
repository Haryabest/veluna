import { generationService } from "@/services/api";
import { ensureTelegramSession } from "@/lib/api-client";
import {
  canShareViaTelegram,
  getTelegramBotLink,
  openTelegramImageShare,
  openTelegramTextShare,
  sharePreparedTelegramMessage,
} from "@/lib/telegram-share";

export async function shareArtImage(imageUrl: string, generationId?: string): Promise<boolean> {
  await ensureTelegramSession();

  if (generationId && canShareViaTelegram()) {
    try {
      const prepared = await generationService.prepareShare(generationId);
      const shared = await sharePreparedTelegramMessage(prepared.prepared_message_id);
      if (shared) return true;
      openTelegramTextShare(getTelegramBotLink(prepared.bot_link), imageUrl);
      return true;
    } catch {
      /* fallback below */
    }
  }

  if (canShareViaTelegram()) {
    openTelegramImageShare(imageUrl, getTelegramBotLink());
    return true;
  }

  if (typeof navigator !== "undefined" && navigator.share) {
    try {
      await navigator.share({
        title: "Veluna",
        text: "Смотри какой арт!",
        url: imageUrl,
      });
      return true;
    } catch {
      /* continue */
    }
  }

  openTelegramImageShare(imageUrl, getTelegramBotLink());
  return true;
}
