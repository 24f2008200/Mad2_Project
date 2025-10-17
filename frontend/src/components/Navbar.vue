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
        <!-- <form class="d-flex" role="search" @submit.prevent="onSearch">
          <input v-model="query" class="form-control me-2" type="search" placeholder="Search" aria-label="Search" />
          <button class="btn btn-outline-success" type="submit">Search</button>
        </form>
        <div class="d-flex justify-content-end">
        </div> -->
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
      <!-- <ul class="navbar-nav">
        <li class="nav-item">
          <button class="btn btn-outline-primary btn-sm" @click="openProfile">Profile</button>
        </li>
        <li class="nav-item">
          <button class="btn btn-sm btn-outline-light ms-2" @click="doLogout">
            Logout
          </button>
        </li>
      </ul> -->
      <form class="d-flex align-items-center gap-3" role="search" @submit.prevent="onSearch">
        <!-- Admin-only search bar -->
        <template v-if="isAdmin">
          <input v-model="query" class="form-control search-input" type="search" placeholder="Search"
            aria-label="Search" />
          <button class="btn btn-search" type="submit">Search</button>
        </template>

        <!-- Always visible buttons -->
        <div class="d-flex gap-2">
          <button class="btn btn-profile" type="button" @click="openProfile">
            Profile
          </button>
          <button class="btn btn-logout" type="button" @click="doLogout">
            Logout
          </button>
        </div>
      </form>


    </div>
  </nav>
  <div>
    <UserProfileModal :userId="userId" :currentUserIsAdmin="currentUserIsAdmin" :show="show" @closed="show = false">
    </UserProfileModal>
  </div>


</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../stores/auth";
import { useSearchStore } from "../stores/search";
import { apiFetch } from "@/api";
import UserProfileModal from '../components/UserProfileModal.vue';
const { isLoggedIn, isAdmin, logout,userName } = useAuth();

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
  return isAdmin.value ? "Welcome to Admin" : userName.value +"'s Dashboard";
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
}
.nav-link {
  color: #fff !important;
}
.nav-link.router-link-active {
  font-weight: bold;
  text-decoration: underline;
}
.btn {
  min-width: 90px;
  height: 38px;
  border-radius: 6px;
  font-weight: 500;
  border: none;
  transition: all 0.25s ease-in-out;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
.btn-search {
  background-color: #0d6efd;
  color: white;
}
.btn-search:hover {
  background-color: #0b5ed7;
  box-shadow: 0 0 8px rgba(13, 110, 253, 0.5);
}
.btn-profile {
  background-color: #20c997;
  color: white;
}
.btn-profile:hover {
  background-color: #17a589;
  box-shadow: 0 0 8px rgba(32, 201, 151, 0.5);
}
.btn-logout {
  background-color: #dc3545;
  color: white;
}
.btn-logout:hover {
  background-color: #bb2d3b;
  box-shadow: 0 0 8px rgba(220, 53, 69, 0.5);
}
.search-input {
  width: 200px;
  border-radius: 6px;
  border: 1px solid #555;
  background-color: #2c2f33;
  color: white;
  padding: 6px 10px;
  transition: all 0.2s;
}
.search-input:focus {
  outline: none;
  border-color: #0d6efd;
  box-shadow: 0 0 5px rgba(13, 110, 253, 0.6);
}
</style>