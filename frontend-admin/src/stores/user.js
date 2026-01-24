import { defineStore } from "pinia";
import { ref } from "vue";
import { login as loginApi, logout as logoutApi, getProfile } from "@/api/auth";

export const useUserStore = defineStore("user", () => {
  const token = ref(localStorage.getItem("token") || "");
  const user = ref(JSON.parse(localStorage.getItem("user") || "null"));

  const login = async (credentials) => {
    const res = await loginApi(credentials);
    if (res.success) {
      token.value = res.data.access_token;
      user.value = res.data.user;
      localStorage.setItem("token", res.data.access_token);
      localStorage.setItem("user", JSON.stringify(res.data.user));
    }
    return res;
  };

  const logout = async () => {
    try {
      await logoutApi();
    } catch (e) {
      // ignore
    }
    token.value = "";
    user.value = null;
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  };

  const fetchProfile = async () => {
    const res = await getProfile();
    if (res.success) {
      user.value = res.data;
      localStorage.setItem("user", JSON.stringify(res.data));
    }
    return res;
  };

  return { token, user, login, logout, fetchProfile };
});
