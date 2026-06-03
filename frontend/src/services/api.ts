import { apiClient } from "@/lib/api-client";
import type { User } from "@/store/user-store";

export const authService = {
  async authenticateTelegram(initData: string) {
    const { data } = await apiClient.post<{ access_token: string; refresh_token: string }>(
      "/auth/telegram",
      { init_data: initData }
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
};

export const chatListService = {
  async pin(chatId: string, pinned: boolean) {
    const { data } = await apiClient.patch<{ id: string; pinned: boolean; ok: boolean }>(
      `/chats/${chatId}/pin`,
      { pinned }
    );
    return data;
  },

  async rename(chatId: string, title: string) {
    const { data } = await apiClient.patch<{ id: string; title: string; ok: boolean }>(
      `/chats/${chatId}`,
      { title }
    );
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

  async create(characterId: string) {
    const { data } = await apiClient.post("/chats", { character_id: characterId });
    return data;
  },

  async getMessages(chatId: string, limit = 50) {
    const { data } = await apiClient.get(`/chats/${chatId}/messages`, { params: { limit } });
    return data;
  },

  async sendMessage(chatId: string, content: string) {
    const { data } = await apiClient.post(`/chats/${chatId}/messages`, { content });
    return data;
  },
};

export const generationService = {
  async create(payload: { prompt: string; negative_prompt?: string; character_id?: string }) {
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

  async checkout(
    productId: string,
    promoCode?: string,
    paymentMethod: "stars" = "stars"
  ) {
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
      payment_method: paymentMethod,
    });
    return data;
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
export type TopUpPaymentMethod = "stars" | "other";

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
    const { data } = await apiClient.get<{ items: BalanceHistoryItem[]; type: string }>(
      "/users/transactions",
      { params: { type, page } }
    );
    return data;
  },

  async getTopUpQuote(payload: {
    currency_type: TopUpCurrency;
    amount: number;
    promo_code?: string;
  }) {
    const { data } = await apiClient.post<TopUpQuote>("/balance/topup/quote", payload);
    return data;
  },

  async topUpCheckout(payload: {
    currency_type: TopUpCurrency;
    amount: number;
    promo_code?: string;
    payment_method: TopUpPaymentMethod;
    stars_amount: number;
  }) {
    const { data } = await apiClient.post<{
      purchase_id: string;
      invoice_url: string;
      status: string;
      ok: boolean;
    }>("/balance/topup/checkout", payload);
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
