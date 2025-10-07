<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
    <div class="container-fluid mt-4">
      <span class="navbar-brand">
        {{ welcomeText }}
      </span>

      <!-- Public Navbar -->
      <template v-if="!isLoggedIn">
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <RouterLink class="nav-link" to="/api/login">Login</RouterLink>
          </li>
          <li class="nav-item">
            <RouterLink class="nav-link" to="/register">Register</RouterLink>
          </li>
        </ul>
      </template>

      <!-- Show admin-only links -->
      <template v-else-if="isAdmin">
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <RouterLink class="nav-link" to="/api/admin">Home</RouterLink>
          </li>
          <li class="nav-item">
            <RouterLink class="nav-link" to="/api/admin/summary">Summary</RouterLink>
          </li>
          <li class="nav-item d-flex align-items-center ms-3">
            <input class="form-check-input me-1" type="radio" id="searchUser" value="user"
              v-model="searchStore.searchType" />
            <label class="form-check-label text-white" for="searchUser">User</label>
          </li>

          <li class="nav-item d-flex align-items-center ms-3">
            <input class="form-check-input me-1" type="radio" id="searchReservation" value="reservation"
              v-model="searchStore.searchType" />
            <label class="form-check-label text-white" for="searchReservation">Reservation</label>
          </li>
          <li class="nav-item d-flex align-items-center ms-3">
            <input class="form-check-input me-1" type="radio" id="searchReservation" value="lot"
              v-model="searchStore.searchType" />
            <label class="form-check-label text-white" for="searchReservation">Lot</label>
          </li>

          <!-- <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
              Dropdown
            </a>
            <ul class="dropdown-menu">
              <li><a class="dropdown-item" href="#">Action</a></li>
              <li><a class="dropdown-item" href="#">Another action</a></li>
              <li>
                <hr class="dropdown-divider">
              </li>
              <li><a class="dropdown-item" href="#">Something else here</a></li>
            </ul>
          </li> -->
        </ul>
        <form class="d-flex" role="search" @submit.prevent="onSearch">
          <input v-model="query" class="form-control me-2" type="search" placeholder="Search" aria-label="Search" />
          <button class="btn btn-outline-success" type="submit">Search</button>
        </form>
        <div class="d-flex justify-content-end">

        </div>

        <!-- 
      </form> -->


      </template>
      <!-- User Navbar -->
      <template v-else>
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <RouterLink class="nav-link" to="/api/user">Home</RouterLink>
          </li>
          <li class="nav-item">
            <RouterLink class="nav-link" to="/api/user/summary">Summary</RouterLink>
          </li>

        </ul> 
      </template>

      <!-- Shared links -->
      <ul class="navbar-nav">
        <li class="nav-item">
          <!-- <RouterLink class="nav-link" to="/profile">Edit Profile</RouterLink> -->
          <button class="btn btn-outline-primary btn-sm" @click="openProfile">Profile</button>
        </li>
        <li class="nav-item">
          <button class="btn btn-sm btn-outline-light ms-2" @click="doLogout">
            Logout
          </button>
        </li>
      </ul>
    </div>
  </nav>
  <div>
    <UserProfileModal :userId="userId" :currentUserIsAdmin="currentUserIsAdmin" :show="show" @closed="show = false">
    </UserProfileModal>
  </div>


</template>

<script setup>
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../stores/auth";
import { useSearchStore } from "../stores/search";
import { apiFetch } from "@/api";
import { watch } from "vue";
import UserProfileModal from '../components/UserProfileModal.vue';


const { isLoggedIn, isAdmin, logout } = useAuth();

const userId = ref();
const show = ref(false);
let currentUserIsAdmin = ref(false);

const searchStore = useSearchStore();
// const searchType = searchStore.searchType;
const router = useRouter();

const welcomeText = computed(() => {
  if (!isLoggedIn.value) {
    return "Welcome, Guest"
  }
  return isAdmin.value ? "Welcome to Admin" : "Welcome to User"
})

watch(
  () => searchStore.searchType,
  (newVal) => {
    router.push("/api/users"); // navigate once type changes
    searchStore.triggerNavbarAction();
  }
);
function openProfile() {
  const { isAdmin, userName, userId: uid } = useAuth()
  userId.value = parseInt(uid.value)
  currentUserIsAdmin.value = isAdmin.value
  show.value = true

}
const query = ref("")


const onSearch = () => {
 searchStore.searchValue = query.value;
  router.push({ path: "/search", query: { q: query.value } })
  searchStore.triggerSearchAction();
}
// function onSearchByClick() {
//   searchStore.triggerNavbarAction();
// }
async function doLogout() {
  try {
    await apiFetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });
  } catch (e) {
    console.warn("Logout request failed:", e);
  }
  localStorage.removeItem("access_token");
  localStorage.removeItem("is_admin");
  logout();
  router.push("/");
}
</script>

<style scoped>
.navbar-brand {
  font-weight: bold;
  color: #ff4444;
  /* red accent for "Welcome" */
}

.nav-link {
  color: #fff !important;
}

.nav-link.router-link-active {
  font-weight: bold;
  text-decoration: underline;
}
</style>
