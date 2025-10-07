import { createRouter, createWebHistory } from "vue-router";
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



const routes = [
  // Public (general) routes
  { path: "/", component: Home },
  { path: "/api/login", component: Login },
  { path: "/register", name: "Register", component: Register },

  // User routes
  { path: "/api/user", component: UserDashboard, meta: { requiresAuth: true, role: "user" } },
  { path: "/api/user/summary", component: UserSummary, meta: { requiresAuth: true, role: "user" } },
  { path: "/profile", component: Profile, meta: { requiresAuth: true } },

  // Admin routes
  { path: "/api/admin", component: AdminDashboard, meta: { requiresAuth: true, role: "admin" } },
  { path: "/api/users", component: AdminView, meta: { requiresAuth: true, role: "admin" } },
  { path: "/api/admin/summary", component: Summary, meta: { requiresAuth: true } },
  { path: "/search", component: Search, meta: { requiresAuth: true, role: "admin" } }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});


router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("access_token");
  const isAdmin = localStorage.getItem("is_admin") === "true";

  if (to.meta.requiresAuth && !token) {
    // Not logged in → send to login
    return next("/api/login");
  }

  if (to.meta.role === "admin" && !isAdmin) {
    // Logged in but not admin
    return next("/api/user");
  }

  if (to.meta.role === "user" && isAdmin) {
    // Admin trying to access user-only route
    return next("/api/admin");
  }

  next();
});

export default router;
