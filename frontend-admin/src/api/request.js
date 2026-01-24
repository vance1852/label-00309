import axios from "axios";
import { ElMessage } from "element-plus";
import router from "@/router";

const request = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      if (status === 401) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        router.push("/login");
        ElMessage.error("登录已过期，请重新登录");
      } else {
        ElMessage.error(data?.message || "请求失败");
      }
    } else {
      ElMessage.error("网络错误");
    }
    return Promise.reject(error);
  },
);

export default request;
