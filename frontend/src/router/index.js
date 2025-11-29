import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

import Home from "../views/Home.vue";
import Login from "../views/Login.vue";
import Register from "../views/Register.vue";
import AdminDashboard from "../views/AdminDashboard.vue";
import UserDashboard from "../views/UserDashboard.vue";
import AdminView from "../views/AdminView.vue";
import Search from "../views/Search.vue";
import Summary from "../views/Summary.vue";
import Profile from "../views/Profile.vue";
import UserSummary from "../views/UserSummary.vue";
// import { storeToRefs } from "pinia";
// const auth = useAuthStore();
// const { isLoggedIn, isAdmin, userName, userId: uid, token } = storeToRefs(auth);

const routes = [
  // Public routes
  { path: "/", component: Home },
  { path: "/login", component: Login },
  { path: "/register", name: "Register", component: Register },

  // User routes
  { path: "/user", component: UserDashboard, meta: { requiresAuth: true, role: "user" } },
  { path: "/user/summary", component: UserSummary, meta: { requiresAuth: true, role: "user" } },
  { path: "/profile", component: Profile, meta: { requiresAuth: true } },

  // Admin routes
  { path: "/admin", component: AdminDashboard, meta: { requiresAuth: true, role: "admin" } },
  { path: "/views", component: AdminView, meta: { requiresAuth: true, role: "admin" } },
  { path: "/admin/summary", component: Summary, meta: { requiresAuth: true, role: "admin" } },
  { path: "/search", component: Search, meta: { requiresAuth: true, role: "admin" } },

  // { path: "/tasks", component: TaskDashboard, meta: { requiresAuth: true }   },

  { path: "/tasks", component: () => import("../components/CeleryTaskDashboard.vue") },


  //  Catch-all: redirect any unknown URL (e.g., /api/login) 
  { path: "/:pathMatch(.*)*", redirect: "/" }
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

// ----------------------------------------------------
// Global Navigation Guard
// ----------------------------------------------------
router.beforeEach((to, from, next) => {
  const auth = useAuthStore();

  // require login
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return next("/login");
  }

  // admin-only route
  if (to.meta.role === "admin" && !auth.isAdmin) {
    return next("/user");
  }

  // user-only route
  if (to.meta.role === "user" && auth.isAdmin) {
    return next("/admin");
  }

  next();
});
router.afterEach((to) => {
  console.log(" Navigated to:", to.fullPath);
});
export default router;
