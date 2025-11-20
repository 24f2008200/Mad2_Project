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
import { useRouter } from "vue-router";
import { useAuth } from "@/stores/auth";
import { useSearchStore } from "@/stores/search";
import SearchBox from "./SearchBox.vue";
import AdminNavLinks from "./AdminNavLinks.vue";
import UserProfileModal from "./UserProfileModal.vue";

const { isLoggedIn, isAdmin, logout, userName } = useAuth();
const searchStore = useSearchStore();
const router = useRouter();

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
