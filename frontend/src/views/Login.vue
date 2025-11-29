<template>
  <div class="container mt-5">
    <h2>Login</h2>
    <form @submit.prevent="doLogin">
      <div class="mb-3">
        <label class="form-label">Email</label>
        <input v-model="email" type="email" class="form-control" required />
      </div>
      <div class="mb-3">
        <label class="form-label">Password</label>
        <input v-model="password" type="password" class="form-control" required />
      </div>
      <button class="btn btn-primary" type="submit">Login</button>
    </form>
    <p v-if="error" class="text-danger mt-2">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from "vue";
// import { useRouter } from "vue-router";
import { router } from "@/router";
import { useAuthStore} from "../stores/auth";
import apiClient from "@/apiClient";
import { useSearchStore } from "../stores/search";
import { storeToRefs } from "pinia";
// const auth = useAuthStore();
// const { isLoggedIn, isAdmin, userName, userId: uid, token, login } = storeToRefs(auth);
const { login } = useAuthStore();

const email = ref("");
const password = ref("");
const error = ref(null);
// const router = useRouter();
const searchStore = useSearchStore();

const today = new Date()
const endDate = ref(today.toISOString().substring(0, 10))

const start = new Date()
start.setMonth(start.getMonth() - 1)
const startDate = ref(start.toISOString().substring(0, 10))



async function doLogin() {
  searchStore.startDate = startDate.value;
  searchStore.endDate = endDate.value;
  console.log("Start Date:", searchStore.startDate);
  try {
    const data =await apiClient.post("/auth/login", {
      email: email.value,
      password: password.value,
    });
    // const res = await apiFetch("/api/auth/login", {
    //   method: "POST",
    //   headers: { "Content-Type": "application/json" },
    //   credentials: "include", // send cookies/session if backend sets them
    //   body: JSON.stringify({
    //     email: email.value,
    //     password: password.value,
    //   }),
    // });



    // Try parsing JSON safely
    // const data = await res.json().catch(() => null);


    // if (!res.ok) {
    //   error.value = data?.message || "Invalid login credentials";
    //   return;
    // }

    login(data);
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("current_user", JSON.stringify(data.user));

    // Redirect based on role
    if (data.user.is_admin) {
      router.push("/admin");
    } else {
      router.push("/user");
    }
  } catch (err) {
    console.error("Login failed:", err);
    error.value = "Something went wrong.";
  }
}
</script>

