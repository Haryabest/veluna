import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { API_URL } from "./constants";
import { translateApiError } from "./i18n";
import { getTelegramInitData } from "./telegram-webapp";
import { useAuthStore } from "@/store/auth-store";

export function isLocalDevHost(): boolean {
  if (typeof window === "undefined") return false;
  const host = window.location.hostname;
  return host === "localhost" || host === "127.0.0.1";
}

function persistTokens(access: string, refresh: string) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
  useAuthStore.getState().setTokens(access, refresh);
}

async function sessionFromExistingToken(): Promise<boolean> {
  const token = localStorage.getItem("access_token");
  if (!token) return false;
  try {
    const { authService } = await import("@/services/api");
    await authService.getMe();
    const refresh = localStorage.getItem("refresh_token") ?? "";
    useAuthStore.getState().setTokens(token, refresh);
    return true;
  } catch {
    localStorage.removeItem("access_token");
    return false;
  }
}

async function sessionFromRefresh(): Promise<boolean> {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) return false;
  try {
    const { data } = await axios.post<{ access_token: string; refresh_token: string }>(
      `${API_URL}/auth/refresh`,
      null,
      { params: { refresh_token: refreshToken } }
    );
    persistTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    return false;
  }
}

async function sessionFromDev(): Promise<boolean> {
  if (!isLocalDevHost()) return false;
  const { authService } = await import("@/services/api");
  const tokens = await authService.authenticateDev();
  persistTokens(tokens.access_token, tokens.refresh_token);
  return true;
}

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

/** Ensure a valid API session before pay / generation. */
export async function ensureTelegramSession(): Promise<boolean> {
  if (typeof window === "undefined") return false;
  try {
    if (await sessionFromExistingToken()) return true;
    if (await sessionFromRefresh()) return true;

    const initData = getTelegramInitData();
    if (initData) {
      try {
        const access = await reauthFromTelegram();
        if (access) return true;
      } catch {
        /* try dev / fail below */
      }
    }

    if (await sessionFromDev()) return true;
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
  persistTokens(data.access_token, data.refresh_token);
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
            useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
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
        const viaTunnel =
          typeof window !== "undefined" &&
          !/localhost|127\.0\.0\.1/.test(window.location.hostname);
        return {
          code: "BACKEND_OFFLINE",
          message: viaTunnel
            ? "Сервер API недоступен. Туннель Pinggy мог истечь — на ПК: .\\scripts\\redeploy.ps1 -Quick"
            : "Сервер API недоступен. Запустите .\\scripts\\veluna-up.ps1 -HostOnly, затем .\\scripts\\restart-frontend.ps1",
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
