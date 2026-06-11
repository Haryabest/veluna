import { apiClient } from "@/lib/api-client";
import { getTelegramInitData } from "@/lib/telegram-webapp";
import type { User } from "@/store/user-store";

export const authService = {
  async authenticateTelegram(initData: string) {
    const { data } = await apiClient.post<{ access_token: string; refresh_token: string }>(
      "/auth/telegram",
      { init_data: initData }
    );
    return data;
  },

  /** Localhost dev when opened outside Telegram WebApp */
  async authenticateDev() {
    const { data } = await apiClient.post<{ access_token: string; refresh_token: string }>(
      "/auth/dev"
    );
    return data;
  },

  async getMe(): Promise<User> {
    const { data } = await apiClient.get<User>("/users/me");
    return data;
  },
};

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export const characterService = {
  async list(page = 1, category?: string) {
    const { data } = await apiClient.get("/characters", { params: { page, category } });
    return data;
  },

  async getById(id: string) {
    const { data } = await apiClient.get(`/characters/${id}`);
    return data;
  },

  async getBySlug(slug: string) {
    const { data } = await apiClient.get(`/characters/slug/${slug}`);
    return data;
  },

  async resolve(idOrSlug: string) {
    if (UUID_RE.test(idOrSlug)) {
      try {
        return await this.getById(idOrSlug);
      } catch {
        return this.getBySlug(idOrSlug);
      }
    }
    return this.getBySlug(idOrSlug);
  },

  async listScenarios(characterId: string) {
    const { data } = await apiClient.get(`/characters/${characterId}/scenarios`);
    return data;
  },

  async listNarrators(characterId: string) {
    const { data } = await apiClient.get(`/characters/${characterId}/narrators`);
    return data;
  },
};

export type ChatListApiItem = {
  id: string;
  character_id: string;
  character_name: string;
  scenario_id?: string | null;
  scenario_title?: string | null;
  narrator_id?: string | null;
  narrator_name?: string | null;
  character_avatar_url?: string | null;
  display_title: string;
  is_pinned?: boolean;
  is_system?: boolean;
  last_message_preview?: string | null;
  last_message_at?: string | null;
  unread?: number;
};

export const chatListService = {
  async pin(chatId: string, pinned: boolean) {
    const { data } = await apiClient.patch<ChatListApiItem>(`/chats/${chatId}/pin`, { pinned });
    return data;
  },

  async rename(chatId: string, title: string) {
    const { data } = await apiClient.patch<ChatListApiItem>(`/chats/${chatId}`, { title });
    return data;
  },

  async remove(chatId: string) {
    const { data } = await apiClient.delete<{ id: string; deleted: boolean; ok: boolean }>(
      `/chats/${chatId}`
    );
    return data;
  },
};

export const chatService = {
  async list(page = 1) {
    const { data } = await apiClient.get("/chats", { params: { page } });
    return data;
  },

  async create(characterId: string, scenarioId: string, narratorId: string) {
    const { data } = await apiClient.post("/chats", {
      character_id: characterId,
      scenario_id: scenarioId,
      narrator_id: narratorId,
    });
    return data;
  },

  async switchScenario(chatId: string, scenarioId: string) {
    const { data } = await apiClient.patch(`/chats/${chatId}/scenario`, { scenario_id: scenarioId });
    return data;
  },

  async switchNarrator(chatId: string, narratorId: string) {
    const { data } = await apiClient.patch(`/chats/${chatId}/narrator`, { narrator_id: narratorId });
    return data;
  },

  async get(chatId: string) {
    const { data } = await apiClient.get(`/chats/${chatId}`);
    return data;
  },

  async getMessages(chatId: string, limit = 50) {
    const { data } = await apiClient.get(`/chats/${chatId}/messages`, { params: { limit } });
    return data;
  },

  async sendMessage(chatId: string, content: string, replyToId?: string) {
    const { data } = await apiClient.post(`/chats/${chatId}/messages`, {
      content,
      reply_to_id: replyToId ?? null,
    });
    return data as {
      user_message: {
        id: string;
        chat_id: string;
        role: string;
        content: string;
        reply_to_id?: string | null;
        reply_preview?: { id: string; role: string; content: string } | null;
        created_at: string;
      };
      ai_reply_status: string;
    };
  },

  async deleteMessage(chatId: string, messageId: string, scope: "self" | "all") {
    const { data } = await apiClient.delete(`/chats/${chatId}/messages/${messageId}`, {
      params: { scope },
    });
    return data;
  },

  async attachArt(chatId: string, generationId: string) {
    const { data } = await apiClient.post(`/chats/${chatId}/art`, { generation_id: generationId });
    return data;
  },
};

export type UserFinanceStats = {
  balance: { gems: number; credits: number };
  spent: { gems: number; credits: number };
  deposited: { gems: number; credits: number };
  purchases: {
    completed_count: number;
    stars_total: number;
    gems_total: number;
    credits_total: number;
  };
  lifetime: { total_earned: number; total_spent: number };
};

export const userService = {
  async getFinanceStats() {
    const { data } = await apiClient.get<UserFinanceStats>("/users/finance");
    return data;
  },

  /** @deprecated use getFinanceStats */
  async getSpending() {
    return this.getFinanceStats();
  },
};

export const generationService = {
  async create(payload: { prompt: string; negative_prompt?: string; character_id?: string; model_id?: string; width?: number; height?: number }) {
    const { data } = await apiClient.post("/generations", payload);
    return data;
  },

  async getById(id: string) {
    const { data } = await apiClient.get(`/generations/${id}`);
    return data;
  },

  async list(page = 1) {
    const { data } = await apiClient.get("/generations", { params: { page } });
    return data;
  },

  async prepareShare(id: string) {
    const { data } = await apiClient.post<{ prepared_message_id: string; bot_link?: string }>(
      `/generations/${id}/share`
    );
    return data;
  },
};

export const shopService = {
  async listProducts() {
    const { data } = await apiClient.get("/shop/products");
    return data;
  },

  async validatePromo(code: string) {
    const { data } = await apiClient.post<{ valid: boolean; discount_percent: number; message: string }>(
      "/shop/promo/validate",
      { code }
    );
    return data;
  },

  async checkout(productId: string, promoCode?: string) {
    const { data } = await apiClient.post<{
      purchase_id: string;
      invoice_url: string;
      stars_amount: number;
      usd_amount: number;
      product_name: string;
      gems_amount: number;
      credits_amount: number;
    }>("/shop/checkout", {
      product_id: productId,
      promo_code: promoCode || undefined,
      payment_method: "stars",
      init_data: getTelegramInitData() ?? undefined,
    });
    return data;
  },
};

export const catalogService = {
  async getVersion() {
    const { data } = await apiClient.get<{ version: number }>("/catalog/version");
    return data.version;
  },
};

export interface UserBalance {
  gems: number;
  credits: number;
}

export interface BalanceHistoryItem {
  id: string;
  amount: number;
  currency: "gems" | "credits";
  description: string;
  created_at: string;
}

export type TopUpCurrency = "gems" | "credits";
export interface TopUpQuote {
  currency_type: TopUpCurrency;
  amount: number;
  promo_code: string | null;
  discount_percent: number;
  promo_valid: boolean;
  promo_message: string | null;
  stars_amount: number;
  usd_amount: number;
  ok: boolean;
}

export const balanceService = {
  async get(): Promise<UserBalance> {
    const { data } = await apiClient.get<UserBalance>("/users/balance");
    return data;
  },

  async getHistory(type: "expense" | "deposit", page = 1) {
    const { data } = await apiClient.get<{
      items: Array<{
        id: string;
        amount: number;
        description: string;
        created_at: string;
        type?: string;
        currency?: string;
        metadata?: Record<string, unknown>;
      }>;
    }>("/users/transactions", { params: { type, page } });

    const formatDescription = (raw: string) => {
      if (raw === "Image generation") return "Генерация изображения";
      if (raw.startsWith("Message to ")) return `Чат с ${raw.replace("Message to ", "")}`;
      if (raw.startsWith("Narrator: ")) return raw.replace("Narrator: ", "Рассказчик: ");
      if (raw === "Welcome bonus") return "Приветственный бонус";
      return raw || "Операция";
    };

    const items: BalanceHistoryItem[] = (data.items ?? []).map((t) => {
      const raw = t as {
        currency?: string;
        metadata?: Record<string, unknown>;
        description?: string;
      };
      const metaCurrency = raw.metadata?.currency;
      const desc = (raw.description || "").toLowerCase();
      let currency: "gems" | "credits" = "gems";
      if (raw.currency === "credits" || metaCurrency === "credits") {
        currency = "credits";
      } else if (raw.currency === "gems" || metaCurrency === "gems") {
        currency = "gems";
      } else if (desc.includes("image generation") || desc.includes("генерац")) {
        currency = "gems";
      } else if (desc.includes("сообщение") || desc.includes("narrator") || desc.includes("рассказчик")) {
        currency = "credits";
      }
      return {
        id: t.id,
        amount: t.amount,
        currency,
        description: formatDescription(t.description),
        created_at: t.created_at,
      };
    });
    return { items, type };
  },

  async getTopUpQuote(payload: {
    currency_type: TopUpCurrency;
    amount: number;
    promo_code?: string;
  }) {
    const { data } = await apiClient.post<TopUpQuote>("/payments/topup/quote", payload);
    return data;
  },

  async topUpCheckout(payload: {
    currency_type: TopUpCurrency;
    amount: number;
    promo_code?: string;
    stars_amount: number;
  }) {
    const { data } = await apiClient.post<{
      purchase_id: string;
      invoice_url: string;
      status: string;
      ok: boolean;
    }>("/payments/topup/checkout", {
      ...payload,
      payment_method: "stars",
    });
    return data;
  },
};

export const paymentService = {
  async getBalance() {
    const { data } = await apiClient.get("/payments/balance");
    return data;
  },

  async getTransactions(page = 1) {
    const { data } = await apiClient.get("/payments/transactions", { params: { page } });
    return data;
  },
};

export const adminService = {
  async getStats() {
    const { data } = await apiClient.get("/admin/stats");
    return data;
  },

  async listUsers(page = 1) {
    const { data } = await apiClient.get("/admin/users", { params: { page } });
    return data;
  },
};
