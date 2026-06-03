import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { API_URL } from "./constants";
import { translateApiError } from "./i18n";
import { getTelegramInitData } from "./telegram-webapp";

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
    ...(API_URL.includes("ngrok") ? { "ngrok-skip-browser-warning": "1" } : {}),
  },
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined" && config.headers) {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    const initData = getTelegramInitData();
    if (initData) {
      config.headers["X-Telegram-Init-Data"] = initData;
    }
  }
  return config;
});

/** Re-login from Telegram initData before pay / after 401. */
export async function ensureTelegramSession(): Promise<boolean> {
  try {
    return (await reauthFromTelegram()) !== null;
  } catch {
    return false;
  }
}

async function reauthFromTelegram(): Promise<string | null> {
  const initData = getTelegramInitData();
  if (!initData) return null;
  const { data } = await axios.post<{ access_token: string; refresh_token: string }>(
    `${API_URL}/auth/telegram`,
    { init_data: initData }
  );
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  return data.access_token;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined" && error.config) {
      const cfg = error.config as InternalAxiosRequestConfig & { _retried?: boolean };
      if (!cfg._retried) {
        cfg._retried = true;
        const initData = getTelegramInitData();
        if (initData) {
          cfg.headers["X-Telegram-Init-Data"] = initData;
        }
        try {
          const access = await reauthFromTelegram();
          if (access) {
            cfg.headers.Authorization = `Bearer ${access}`;
            return apiClient(cfg);
          }
        } catch {
          /* try refresh below */
        }
        const refreshToken = localStorage.getItem("refresh_token");
        if (refreshToken) {
          try {
            const { data } = await axios.post(`${API_URL}/auth/refresh`, null, {
              params: { refresh_token: refreshToken },
            });
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("refresh_token", data.refresh_token);
            cfg.headers.Authorization = `Bearer ${data.access_token}`;
            return apiClient(cfg);
          } catch {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
          }
        }
      }
    }
    return Promise.reject(error);
  }
);

export interface ApiError {
  code: string;
  message: string;
}

export function getApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "object" && detail !== null) {
      return {
        code: detail.code || "ERROR",
        message: detail.message || "Неизвестная ошибка",
      };
    }
    return { code: "ERROR", message: translateApiError(error.message) };
  }
  return { code: "ERROR", message: "Неизвестная ошибка" };
}
