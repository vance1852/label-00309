import { createRouter, createWebHistory } from "vue-router";
import { useUserStore } from "@/stores/user";

const routes = [
  {
    path: "/login",
    name: "Login",
    component: () => import("@/views/Login.vue"),
    meta: { requiresAuth: false },
  },
  {
    path: "/",
    component: () => import("@/views/Layout.vue"),
    redirect: "/dashboard",
    children: [
      {
        path: "dashboard",
        name: "Dashboard",
        component: () => import("@/views/Dashboard.vue"),
        meta: { title: "仪表盘" },
      },
      {
        path: "servers",
        name: "Servers",
        component: () => import("@/views/Servers.vue"),
        meta: { title: "服务器管理" },
      },
      {
        path: "inspections",
        name: "Inspections",
        component: () => import("@/views/Inspections.vue"),
        meta: { title: "巡检记录" },
      },
      {
        path: "alerts",
        name: "Alerts",
        component: () => import("@/views/Alerts.vue"),
        meta: { title: "告警设置" },
      },
      {
        path: "schedule",
        name: "Schedule",
        component: () => import("@/views/Schedule.vue"),
        meta: { title: "调度设置" },
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const userStore = useUserStore();

  if (to.meta.requiresAuth === false) {
    next();
  } else if (!userStore.token) {
    next("/login");
  } else {
    next();
  }
});

export default router;
