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
  if (typeof window === "undefined") return false;
  if (localStorage.getItem("access_token")) return true;
  try {
    const initData = getTelegramInitData();
    if (initData) {
      return (await reauthFromTelegram()) !== null;
    }
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1") {
      const { authService } = await import("@/services/api");
      const tokens = await authService.authenticateDev();
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      return true;
    }
    return false;
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
    const detail = error.response?.data as { detail?: { code?: string } } | undefined;
    if (detail?.detail?.code === "ACCOUNT_BANNED") {
      return Promise.reject(error);
    }

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
  ban_reason?: string | null;
  banned_until?: string | null;
}

export function getApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "object" && detail !== null) {
      return {
        code: detail.code || "ERROR",
        message: detail.message || "Неизвестная ошибка",
        ban_reason: detail.ban_reason ?? null,
        banned_until: detail.banned_until ?? null,
      };
    }
    if (typeof detail === "string" && detail) {
      return { code: "ERROR", message: detail };
    }
    if (!error.response) {
      const code = (error as { code?: string }).code;
      if (code === "ECONNREFUSED" || error.message.includes("Network Error")) {
        return {
          code: "BACKEND_OFFLINE",
          message:
            "Сервер API недоступен. Запустите .\\scripts\\veluna-up.ps1, затем .\\scripts\\restart-frontend.ps1 (Docker: порт 8020).",
        };
      }
    }
    const status = error.response?.status;
    if (
      (status === 500 || status === 502 || status === 503) &&
      typeof error.response?.data === "string"
    ) {
      return {
        code: "ERROR",
        message:
          "Ошибка сервера генерации. Проверьте логи backend и примените миграции: .\\scripts\\veluna-up.ps1 -SkipBuild",
      };
    }
    return { code: "ERROR", message: translateApiError(error.message) };
  }
  return { code: "ERROR", message: "Неизвестная ошибка" };
}
