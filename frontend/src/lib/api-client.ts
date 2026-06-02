import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { API_URL } from "./constants";
import { translateApiError } from "./i18n";

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
    ...(API_URL.includes("ngrok") ? { "ngrok-skip-browser-warning": "1" } : {}),
  },
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh`, null, {
            params: { refresh_token: refreshToken },
          });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${data.access_token}`;
            return apiClient(error.config);
          }
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
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
