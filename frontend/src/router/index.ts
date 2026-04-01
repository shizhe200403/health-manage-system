import { createRouter, createWebHistory } from "vue-router";

function resolveDefaultRoute() {
  const role = localStorage.getItem("user_role");
  const isSuperuser = localStorage.getItem("user_is_superuser") === "true";
  const isStaff = localStorage.getItem("user_is_staff") === "true";
  return role === "admin" || isSuperuser || isStaff ? "/ops" : "/";
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: () => import("../views/LoginView.vue") },
    { path: "/", component: () => import("../views/HomeView.vue") },
    { path: "/recipes", component: () => import("../views/RecipesView.vue") },
    { path: "/favorites", component: () => import("../views/FavoritesView.vue") },
    { path: "/records", component: () => import("../views/RecordsView.vue") },
    { path: "/goals", component: () => import("../views/GoalsView.vue") },
    { path: "/community", component: () => import("../views/CommunityView.vue") },
    { path: "/reports", component: () => import("../views/ReportsView.vue") },
    { path: "/profile", component: () => import("../views/ProfileView.vue") },
    { path: "/assistant", component: () => import("../views/AssistantView.vue") },
    { path: "/ops", component: () => import("../views/AdminDashboardView.vue"), meta: { requiresAdmin: true } },
    { path: "/ops/community", component: () => import("../views/AdminCommunityView.vue"), meta: { requiresAdmin: true } },
    { path: "/ops/logs", component: () => import("../views/AdminOperationLogsView.vue"), meta: { requiresAdmin: true } },
    { path: "/ops/reports", component: () => import("../views/AdminOpsReportsView.vue"), meta: { requiresAdmin: true } },
    { path: "/ops/recipes", component: () => import("../views/AdminRecipesView.vue"), meta: { requiresAdmin: true } },
    { path: "/ops/users", component: () => import("../views/AdminUsersView.vue"), meta: { requiresAdmin: true } },
  ],
});

router.beforeEach((to) => {
  const token = localStorage.getItem("access_token");
  if (!token && to.path !== "/login") {
    return "/login";
  }
  if (token && to.path === "/login") {
    return resolveDefaultRoute();
  }
  if (to.meta.requiresAdmin) {
    const role = localStorage.getItem("user_role");
    const isSuperuser = localStorage.getItem("user_is_superuser") === "true";
    const isStaff = localStorage.getItem("user_is_staff") === "true";
    if ((role || isSuperuser || isStaff) && role !== "admin" && !isSuperuser && !isStaff) {
      return "/";
    }
  }
  return true;
});

export default router;
