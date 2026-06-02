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

export const characterService = {
  async list(page = 1, category?: string) {
    const { data } = await apiClient.get("/characters", { params: { page, category } });
    return data;
  },

  async getById(id: string) {
    const { data } = await apiClient.get(`/characters/${id}`);
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
