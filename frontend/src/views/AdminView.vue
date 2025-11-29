<template>
  <div class="container-fluid mt-4">
    <h2>{{ title }} Search</h2>
    <!-- User results or Reservation results or Lot results-->
    <div v-if="activeColumns" class="row justify-content-center mb-4">
      <div class="col-12 col-lg-10">
        <div class="table-responsive">
          <DataTable :columns="activeColumns" :rows="results" @action-click="handleAction" />
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
import { ref, onMounted, onUnmounted, computed } from "vue";
import apiClient from '@/apiClient';
import { useSearchStore } from "../stores/search";
import DataTable from "@/components/DataTable.vue";
import RowEditor from "@/components/RowEditor.vue";

const userCols = [

  { key: "id", label: "ID", filterType: "select", type: "noedit" },
  { key: "name", label: "Name", type: "text" },
  { key: "mobile", label: "Mobile", type: "number" },
  { key: "address", label: "Address", type: "text" },
  { key: "email", label: "E-Mail", type: "text" },
  { key: "billing", label: "Revenue" },
  { key: "last_login", label: "Last Seen" },
  {key:"received_reminders", label:"Reminders Sent", noshow: true},
  {key:"reminder_time", label:"Reminder Time", noshow: true},
  {key:"google_chat_webhook", label:"Google Chat Webhook", noshow: true},
  {key:"password", label:"Password",type: "password", noshow: true},

  { key: "edit", label: "Edit", type: "action" },
];

const reservationCols = [

  { key: "id", label: "ID", filterType: "select", type: "noedit" },
  { key: "label", label: "Spot", type: "text" },
  { key: "user_name", label: "User", type: "text" },
  { key: "vehicle_number", label: "Vechile", type: "text" },
  { key: "start_time", label: "From", type: "text" },
  { key: "end_time", label: "To", type: "text" },
  { key: "driver_name", label: "Driver", type: "text" },
  { key: "driver_contact", label: "Contact", type: "number" },
  { key: "total_earnings", label: "Revenue", type: "number" },
  { key: "edit", label: "Edit", type: "action" , noshow: true},
];
const lotCols = [
  { key: "id", label: "ID", filterType: "select", type: "noedit" },
  { key: "name", label: "Name", type: "text" },
  { key: "address", label: "Address", type: "text" },
  { key: "number_of_spots", label: "Total Spots", type: "number" },
  { key: "available_spots", label: "Available", type: "noedit" },
  { key: "occupied_spots", label: "Occupied", type: "noedit" },
  { key: "price", label: "Price", type: "number" },
  { key: "edit", label: "Edit", type: "action" }
];
const reminderCols = [
  { key: "id", label: "ID", type: "noedit" },
  { key: "user_id", label: "User ID", type: "number" },
  { key: "user_name", label: "User", type: "text" },
  { key: "scheduled_at", label: "Scheduled", type: "text" },
  { key: "status", label: "Status", type: "text" },
  { key: "sent_at", label: "Sent At", type: "text" },
  { key: "error_message", label: "Error", type: "text" }
]

const token = ref(localStorage.getItem("access_token") || "");


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
  searchStore.setNavbarAction(performSearch); // AdminView operations. Call back to performSearch
  searchStore.setOpCode(searchStore.searchType);
  console.log('Mounted: ', searchStore.searchType);
  performSearch();
})

onUnmounted(() => {
  // Clean up when leaving page
  searchStore.setNavbarAction(null)
})


const columnsMap = {
  user: userCols,
  reservation: reservationCols,
  lot: lotCols,
  reminder: reminderCols,
};

const activeColumns = computed(() => {
  return columnsMap[searchStore.searchType] || null;
});


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
  } else if (searchType === 'reminder') {
    editorTitle.value = "Edit Reminder Log"
    editorFields.value = reminderCols
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
  if (searchStore.opCode === 'user') {
    if (updatedRow.password && updatedRow.password.trim() !== "") {
    updatedRow.confirm_password = updatedRow.password;
  }
    const url = `/user/profile/${updatedRow.id}`;
    apiClient.put(url, updatedRow).then(response => {
      console.log("User updated successfully:", response.data);
    }).catch(error => {
      console.error("Error updating user:", error);
    });
  } else if (searchStore.opCode === 'lot') {
    const url = `/admin/lots/${updatedRow.id}`;
    apiClient.put(url, updatedRow).then(response => {
      console.log("Lot updated successfully:", response.data);
    }).catch(error => {
      console.error("Error updating lot:", error);
    });
  } else if (searchStore.opCode === 'reservation') {
    const url = `/admin/reservations/${updatedRow.id}`;
    apiClient.put(url, updatedRow).then(response => {
      console.log("Reservation updated successfully:", response.data);
    }).catch(error => {
      console.error("Error updating reservation:", error);
    });
  } else if (searchStore.opCode === 'reminder') {
    const url = `/admin/reminders/${updatedRow.id}`;
    apiClient.put(url, updatedRow).then(response => {
      console.log("Reminder log updated successfully:", response.data);
    }).catch(error => {
      console.error("Error updating reminder log:", error);
    });
  }
console.log("Saved changes:", updatedRow ,searchStore.opCode );  
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
  
  console.log("Performing search for type:", searchType, "by:", searchBy, "opCode:", searchStore.opCode);
  searchStore.setOpCode(searchType);
  console.log("Set opCode to", searchType);
  const opCode = searchStore.opCode; // reactive opCode
  console.log("opCode is", opCode);


  title.value = searchType === 'user' ? 'User' : searchType === 'lot' ? 'Lot' : searchType === 'reminder' ? 'Reminder' : 'Reservation'
  if (!searchType) {
    alert("Please select search by and enter a value.")
    return
  }

  try {

    console.log("Searching for", searchType, "by", searchBy, "value", searchValue, "opCode", opCode);
    if (searchType == "lot") {
      results.value = await apiClient.get('/admin/lots')
    }
    else {
      results.value = await apiClient.post('/admin/reports')
    }

    searched.value = true;
    console.log(searchType);

    console.log("Before date formatting:", results.value);

    if (results.value.length > 0) {
      tableHeaders.value = Object.keys(results.value[0]);
      console.log("tableHeaders:", tableHeaders.value);
    } else {
      tableHeaders.value = [];
      console.log("No results found.");
    }
  } catch (error) {
    console.error("Search error:", error);
    alert("Error fetching search results.");
  }
}
// Release a spot
async function showDetails(reservationId) {
  const res = await apiFetch(`/api/user/spots`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token.value}` },
    body: JSON.stringify({
      "action": "release",
      "reservation_id": reservationId
    }),
  });
  if (res.ok) {
    reservations.value = reservations.value.map((r) =>
      r.id === reservationId ? { ...r, status: 'completed' } : r
    );
  }
  //fetchReservations();
}
</script>
