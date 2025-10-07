<template>
  <div class="container-fluid mt-4">
    <h2>{{ title }} Search</h2>

    <!-- User results -->
    <div v-if="searchStore.searchType === 'user'" class="row justify-content-center mb-4">
      <div class="col-12 col-lg-10">
        <div class="table-responsive">
          <DataTable :columns="userCols" :rows="results" @action-click="handleAction" />
        </div>
      </div>
    </div>

    <!-- Reservation results -->
    <div v-else-if="searchStore.searchType === 'reservation'" class="row justify-content-center mb-4">
      <div class="col-12 col-lg-10">
        <div class="table-responsive">
          <DataTable :columns="reservationCols" :rows="results" @action-click="handleAction" />
        </div>
      </div>
    </div>

    <!-- Lot results -->
    <div v-else-if="searchStore.searchType === 'lot'" class="row justify-content-center mb-4">
      <div class="col-12 col-lg-10">
        <div class="table-responsive">
          <DataTable :columns="lotCols" :rows="results" @action-click="handleAction" />
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div class="modal fade" id="editModal" tabindex="-1" aria-hidden="true" ref="editModalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-body">
            <RowEditor v-if="editingRow" :title="`Row ID: ${editingRow.id}`" :row="editingRow" :fields="editorFields"
              @save="saveChanges" @cancel="closeModal" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { apiFetch } from "../api";
import { useSearchStore } from "../stores/search";
import DataTable from "@/components/DataTable.vue";
import RowEditor from "@/components/RowEditor.vue";

const userCols = [
  { key: "id", label: "ID", filterType: "select", type: "noedit" },
  { key: "name", label: "Name", type: "text" },
  { key: "mobile", label: "Mobile", type: "number" },
  { key: "address", label: "Address", type: "text" },
  { key: "email", label: "E-Mail", type: "text" },
  { key: "rev", label: "Revenue" },
  { key: "edit", label: "Edit", type: "action" }
];

const reservationCols = [
  { key: "id", label: "ID", filterType: "select", type: "noedit" },
  { key: "label", label: "Spot", type: "text" },
  { key: "user_name", label: "User", type: "text" },
  { key: "vehicle_number", label: "Vechile", type: "text" },
  { key: "start_time", label: "From", type: "text" },
  { key: "end_times", label: "To", type: "text" },
  { key: "driver_name", label: "Driver", type: "text" },
  { key: "driver_contact", label: "Contact", type: "number" },
  { key: "total_earnings", label: "Revenue", type: "number" },
  { key: "edit", label: "Edit", type: "action" }
];
const lotCols = [
  { key: "id", label: "ID", filterType: "select", type: "noedit" },
  { key: "name", label: "Name", type: "text" },
  { key: "address", label: "Address", type: "text" },
  { key: "available_spots", label: "Available", type: "number" },
  { key: "occupied_spots", label: "Occupied", type: "number" },
  { key: "price", label: "Price", type: "number" },
  { key: "edit", label: "Edit", type: "action" }
];

const searchBy = ref("");
//const searchValue = ref("");
const results = ref([]);
const searched = ref(false);
const tableHeaders = ref([]);
const users = ref([]);
const searchStore = useSearchStore();

const title = ref("")

const f_date = (raw) => raw ? new Date(raw).toLocaleString() : '';
onMounted(() => {
  // Register this page’s action
  searchStore.setNavbarAction(performSearch);
  performSearch();
})

onUnmounted(() => {
  // Clean up when leaving page
  searchStore.setNavbarAction(null)
})

const editingRow = ref(null)
const editorTitle = ref("")
const editorFields = ref([])

let modalInstance = null
const editModalEl = ref(null)


function handleAction({ action, id, row }) {
  const searchType = searchStore.searchType; // reactive
  const searchValue = searchStore.searchValue;
  if (searchType === 'user') {
    editorTitle.value = "Edit Parking Lot"
    editorFields.value = userCols
  } else if (searchType === 'lot') {
    editorTitle.value = "Edit  Lot"
    editorFields.value = lotCols
  } else if (searchType === 'reservation') {
    editorTitle.value = "Edit Reservation"
    editorFields.value = reservationCols
  }
  if (action === "edit") {
    editingRow.value = { ...row }
    // editorTitle.value = "Edit Parking Lot"
    // editorFields.value = userCols
    openModal()
  }
}
function saveChanges(updatedRow) {
  // Replace row in rows
  const idx = results.value.findIndex(r => r.id === updatedRow.id)
  if (idx !== -1) results.value[idx] = updatedRow

  closeModal()
}

function openModal() {
  if (!modalInstance) {
    modalInstance = new bootstrap.Modal(editModalEl.value)
  }
  modalInstance.show()
}

function closeModal() {

  if (modalInstance) {
    modalInstance.hide()
  }
}
async function performSearch() {
  const searchType = searchStore.searchType; // reactive searchBy
  const searchValue = searchStore.searchValue;
  const searchBy = searchStore.searchBy;

  title.value = searchType === 'user' ? 'User' : searchType === 'lot' ? 'Lot' : 'Reservation'
  if (!searchType) {
    alert("Please select search by and enter a value.")
    return
  }

  try {
    // Decide endpoint based on global searchType
    const endpoint =
      searchType === "user"
        ? "/api/admin/users"
        : searchType === "reservation"
          ? `/api/admin/search?type=bookings&search_by=${searchBy}&value=${searchValue}`
          : `/api/admin/search?type=lots&search_by=${searchBy}s&value=${searchValue}`;

    const url = `${endpoint}?search_by=${searchType}&value=${encodeURIComponent(
      searchValue
    )}`;
    const response = await apiFetch(url, {
      method: "GET",
      // doDateConversion : true,
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${localStorage.getItem("access_token")}`,
      },
    });

    if (!response.ok) {
      throw new Error("Network response was not ok");
    }

    const data = await response.json();
    results.value = data;
    searched.value = true;

    if (results.value.length > 0) {
      tableHeaders.value = Object.keys(results.value[0]);
    } else {
      tableHeaders.value = [];
    }
  } catch (error) {
    console.error("Search error:", error);
    // alert("Error fetching search results.");
  }
}
// Release a spot
async function showDetails(reservationId) {
  const res = await apiFetch(`/api/user/release/${reservationId}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token.value}` },
  });
  if (res.ok) {
    reservations.value = reservations.value.map((r) =>
      r.id === reservationId ? { ...r, status: 'completed' } : r
    );
  }
  //fetchReservations();
}
</script>
