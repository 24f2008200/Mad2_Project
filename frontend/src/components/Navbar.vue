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
            <RouterLink class="nav-link" to="/login">Login</RouterLink>
          </li>
          <!-- <li>
            <RegisterCopyNew   @closed="show = false">New Register </RegisterCopyNew>
          </li> -->
          <li class="nav-item">
            <RouterLink class="nav-link" to="/register">Register</RouterLink>
          </li>
        </ul>
      </template>


      <!-- Show admin-only links -->
      <template v-else-if="isAdmin">
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <RouterLink class="nav-link" to="/admin">Home</RouterLink>
          </li>
          <li class="nav-item">
            <RouterLink class="nav-link" to="/admin/summary">Summary</RouterLink>
          </li>

          <!-- Replaced radio buttons with clickable links -->
          <li class="nav-item d-flex align-items-center ms-3">
            <RouterLink class="nav-link text-info" :class="{ active: searchStore.searchType === 'user' }"
              @click.prevent="setSearchType('user')" to="/views">
              User
            </RouterLink>
          </li>

          <li class="nav-item d-flex align-items-center ms-3">
            <RouterLink class="nav-link text-info" :class="{ active: searchStore.searchType === 'reservation' }"
              @click.prevent="setSearchType('reservation')" to="/views">
              Reservation
            </RouterLink>
          </li>

          <li class="nav-item d-flex align-items-center ms-3">
            <RouterLink class="nav-link text-info" :class="{ active: searchStore.searchType === 'lot' }"
              @click.prevent="setSearchType('lot')" to="/views">
              Lot
            </RouterLink>
          </li>
          <li class="nav-item d-flex align-items-center ms-3">
            <RouterLink class="nav-link text-info" :class="{ active: searchStore.searchType === 'reminder' }"
              @click.prevent="setSearchType('reminder')" to="/views">
              Reminder Logs
            </RouterLink>
          </li>
          <li class="nav-item">
            <RouterLink class="nav-link" to="/tasks">Tasks</RouterLink>
          </li>
        </ul>
      </template>

      <!-- User Navbar -->
      <template v-else>
        <ul class="navbar-nav me-auto">
          <li class="nav-item d-flex align-items-center ms-3">
            <RouterLink class="nav-link text-info" :class="{ active: searchStore.searchType === 'reservation' }"
              @click.prevent="setSearchType('reservation')" to="/user">
              Home
            </RouterLink>
          </li>
          <!-- <li class="nav-item"> 
            <RouterLink class="nav-link" to="/user">Home</RouterLink>
          </li> -->
          <!-- <li class="nav-item d-flex align-items-center ms-3">
            <RouterLink class="nav-link text-info" :class="{ active: searchStore.searchType === 'reservation' }"
              @click.prevent="setSearchType('reservation')" to="/users">
              Reservation
            </RouterLink>
          </li> -->
          <li class="nav-item">
            <RouterLink class="nav-link" to="/user/summary">Summary</RouterLink>
          </li>
          <li>
            <Button class="btn btn-profile" @click="startExport">Export CSV</Button>
            <!-- <template v-if="exportStatus">
              <span>Status: {{ exportStatus }}</span>
            </template> -->
            <a v-if="downloadUrl" :href="downloadUrl" download="reservations.csv" class="btn btn-link mt-2"
              @click="clearDownloadUrl">
              Download CSV
            </a>


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
      <div class="nav">

        <div style="display:flex; gap:10px; align-items:center">
          <input type="date" v-model="startDate" class="form-control search-input" />
          <input type="date" v-model="endDate" class="form-control search-input" />

          <!-- <button class="btn btn-search"  @click="apply">Apply</button> -->
        </div>
      </div>
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
// import { useRouter } from "vue-router";
import { router } from "@/router";
import { useAuthStore} from "../stores/auth";
import { useSearchStore } from "../stores/search";
import apiClient from '@/apiClient';
import UserProfileModal from '../components/UserProfileModal.vue';
import { storeToRefs } from "pinia";
const auth = useAuthStore();
const { isLoggedIn, isAdmin, userName, userId: uid } = storeToRefs(auth);

const userId = ref();
const show = ref(false);
let currentUserIsAdmin = ref(false);
const exportStatus = ref("");
const downloadUrl = ref("");

const searchStore = useSearchStore();
// const searchType = searchStore.searchType;  
// const router = useRouter();

const today = new Date();
const tomorrow = new Date(today);
tomorrow.setDate(tomorrow.getDate() + 1);

const endDate = ref(tomorrow.toISOString().substring(0, 10));

const start = new Date()
start.setMonth(start.getMonth() - 1)
const startDate = ref(start.toISOString().substring(0, 10))

function apply() {
  searchStore.startDate = startDate.value;
  searchStore.endDate = endDate.value;
  searchStore.triggerNavbarAction(); // Notify views to update
}
const welcomeText = computed(() => {
  if (!isLoggedIn.value) {
    return "Welcome, Guest"
  }
  return userName.value + "'s Dashboard";
})

watch([startDate, endDate], () => {
  apply();
});

watch(
  () => searchStore.searchType,
  (newVal) => {
    console.log("Search type changed to", newVal);
    router.push("/views"); // navigate once type changes
    searchStore.triggerNavbarAction(); // Notify views to update
  }
);
function setSearchType(type) {
  searchStore.setSearchType(type);
  //searchStore.searchType = type;
  console.log("Set search type to", type);
  // router.push("/views");
  // searchStore.triggerNavbarAction(); // Notify views to update
}

function openProfile() {
  //const { isAdmin, userName, userId: uid } = useAuthStore()
  console.log("Opening profile for userId:", uid.value, "isAdmin:", isAdmin.value);
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
// async function doLogout() {
//   router.push({ path: "/login", force: true });
//   console.log("Logging out...");
//   apiClient.post("/auth/logout", {}, { withCredentials: true }).catch((e) => {
//     console.warn("Logout request failed:", e);
//   });
//   localStorage.removeItem("current_user");
//   localStorage.removeItem("access_token");
//   localStorage.removeItem("is_admin");
//   logout();
//   await router.push("/login");  // ensures redirect happens
//   }
async function doLogout() {
  apiClient.post("/auth/logout").catch(() => { });

  const auth = useAuthStore();
  auth.logout();

  await router.replace("/login");
}
async function startExport() {
  exportStatus.value = "Fetching data...";
  downloadUrl.value = "";

  try {
    const json = await apiClient.post("/user/reservations");

    // if (!res.ok) {
    //   exportStatus.value = "Error fetching data";
    //   return;
    // }

    // const json = await res.json();

    if (!Array.isArray(json) || json.length === 0) {
      exportStatus.value = "No data to export";
      return;
    }

    exportStatus.value = "Converting to CSV...";

    // Build CSV
    const csv = convertToCSV(json);

    // Blob URL
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    downloadUrl.value = URL.createObjectURL(blob);

    exportStatus.value = "Ready to download";

  } catch (err) {
    console.error("CSV Export Error:", err);
    exportStatus.value = "Failed to export";
  }
}
function clearDownloadUrl() {
  // let the browser start the download first
  setTimeout(() => {
    URL.revokeObjectURL(downloadUrl.value); // optional cleanup
    downloadUrl.value = "";
    exportStatus.value = "";
  }, 1000); // small delay so download starts
}


// function convertToCSV(data) {
//   const headers = Object.keys(data[0]);
//   const csvRows = [];

//   // Add headers
//   csvRows.push(headers.join(","));

//   // Add rows
//   for (const row of data) {
//     const values = headers.map(header => {
//       const escaped = ("" + row[header]).replace(/"/g, '\\"');
//       return `"${escaped}"`;
//     });
//     csvRows.push(values.join(","));
//   }

//   return csvRows.join("\n");
// }

function convertToCSV(data) {
  const headers = Object.keys(data[0]);

  const escape = (val) =>
    '"' + String(val ?? "").replace(/"/g, '""') + '"';

  const rows = [
    headers.join(","),                                // header row
    ...data.map(row => headers.map(h => escape(row[h])).join(","))  // data rows
  ];

  return rows.join("\n");
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

.nav-link.active {
  font-weight: bold;
  text-decoration: underline;
  color: #0d6efd !important;
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