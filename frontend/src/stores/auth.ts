import { defineStore } from "pinia";
import { getMe, login as loginApi } from "../api/auth";

type UserData = Record<string, any> | null;

export const useAuthStore = defineStore("auth", {
  state: () => ({
    accessToken: localStorage.getItem("access_token") || "",
    refreshToken: localStorage.getItem("refresh_token") || "",
    user: null as UserData,
    ready: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken),
    isPro: (state) => state.user?.plan === "pro",
    aiUsageRemaining: (state): number | null => {
      if (state.user?.plan === "pro") return null;
      return Math.max(0, 30 - (state.user?.ai_monthly_usage ?? 0));
    },
  },
  actions: {
    setTokens(access: string, refresh: string) {
      this.accessToken = access;
      this.refreshToken = refresh;
      localStorage.setItem("access_token", access);
      localStorage.setItem("refresh_token", refresh);
    },
    clearAuth() {
      this.accessToken = "";
      this.refreshToken = "";
      this.user = null;
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user_role");
      localStorage.removeItem("user_is_superuser");
      localStorage.removeItem("user_is_staff");
    },
    async login(username: string, password: string) {
      const response = await loginApi(username, password);
      this.setTokens(response.data.access, response.data.refresh);
      await this.fetchMe();
    },
    async fetchMe() {
      if (!this.accessToken) return;
      const response = await getMe();
      this.user = response.data ?? null;
      this.ready = true;
      localStorage.setItem("user_role", this.user?.role ?? "");
      localStorage.setItem("user_is_superuser", String(Boolean(this.user?.is_superuser)));
      localStorage.setItem("user_is_staff", String(Boolean(this.user?.is_staff)));
    },
  },
});
