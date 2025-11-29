<template>
  <nav class="navbar navbar-dark bg-dark px-3">
    <span class="navbar-brand">{{ welcomeText }}</span>

    <template v-if="isAdmin">
      <AdminNavLinks :active="searchStore.searchType" @change="setSearchType" />
      <SearchBox v-model="searchStore.searchValue" @submit="triggerSearch" />
    </template>

    <template v-else-if="isLoggedIn">
      <UserNavLinks />
    </template>

    <template v-else>
      <PublicNavLinks />
    </template>

    <button class="btn btn-logout" @click="logoutUser">Logout</button>
  </nav>

  <UserProfileModal :userId="profileUserId" :show="showProfile" @closed="showProfile = false" />
</template>

<script setup>
import { computed, ref } from "vue";
// import { useRouter } from "vue-router";
import { router } from "@/router";
import { useAuthStore} from "@/stores/auth";
import { useSearchStore } from "@/stores/search";
import SearchBox from "./SearchBox.vue";
import AdminNavLinks from "./AdminNavLinks.vue";
import UserProfileModal from "./UserProfileModal.vue";
import { storeToRefs } from "pinia";
const auth = useAuthStore();
const { isLoggedIn, isAdmin, userName, userId: uid, token } = storeToRefs(auth);

// const { isLoggedIn, isAdmin, logout, userName } = useAuthStore();
const searchStore = useSearchStore();
// const router = useRouter();

const showProfile = ref(false);
const profileUserId = ref(null);

const welcomeText = computed(() =>
  !isLoggedIn.value
    ? "Welcome, Guest"
    : isAdmin.value
    ? "Admin Panel"
    : `${userName.value}'s Dashboard`
);

function setSearchType(type) {
  searchStore.searchType = type;
  searchStore.triggerNavbarAction();
  router.push("/users");
}

function triggerSearch() {
  searchStore.triggerSearchAction();
}

async function logoutUser() {
  logout();
  router.push("/");
}
</script>
