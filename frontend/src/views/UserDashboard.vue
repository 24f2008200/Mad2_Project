<template>
  <div class="container-fluid mt-4">
    <!-- <h2 class="mb-4">{{ currentUser["name"] }} Dashboard</h2> -->

    <!-- Parking Lots by Pin Code -->
    <div class="card">
      <div class="card-header bg-success text-white">
        Search Parking Lots by Pin Code
      </div>
      <div class="card-body">
        <div class="row mb-3">
          <div class="col-md-6">
            <select v-model="selectedPin" class="form-select" @change="fetchLots">
              <option disabled value="">Select Pin Code</option>
              <option v-for="pin in pinCodes" :key="pin" :value="pin">
                {{ pin }}
              </option>
            </select>
          </div>
        </div>
        <!-- Booking Modal -->
        <div class="modal fade" id="bookingModal" tabindex="-1">
          <div class="modal-dialog">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">Book Parking Slot</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
              </div>
              <div class="modal-body">
                <form @submit.prevent="confirmBooking">
                  <div class="mb-3">
                    <label class="form-label">Vehicle Number</label>
                    <input v-model="form.vehicle_no" type="text" class="form-control" required />
                  </div>
                  <div class="mb-3">
                    <label class="form-label">Driver Name</label>
                    <input v-model="form.driver_name" type="text" class="form-control" required />
                  </div>
                  <div class="mb-3">
                    <label class="form-label">Driver Contact</label>
                    <input v-model="form.driver_contact" type="text" class="form-control" required />
                  </div>
                </form>
              </div>
              <div class="modal-footer">
                <button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button class="btn btn-primary" @click="confirmBooking">Confirm Booking</button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="lots.length">
          <h5>Parking Lots @ {{ selectedPin }}</h5>
          <table class="table table-bordered">
            <thead>
              <tr>
                <th>ID</th>
                <th>Address</th>
                <th>Availability</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="lot in lots" :key="lot.id">
                <td>{{ lot.id }}</td>
                <td>{{ lot.address }}</td>
                <td>{{ lot.available_spots }}</td>
                <td>
                  <button class="btn btn-sm btn-primary me-2" :disabled="lot.available_spots === 0"
                    @click="openBookingModal(lot)">
                    Book
                  </button>

                  <button class="btn btn-sm btn-secondary" @click="closeDropdown()">
                    Close
                  </button>
                </td>

              </tr>
            </tbody>
          </table>
        </div>

        <p v-else class="text-muted">No lots available for this pin code.</p>
      </div>
    </div>
    <!-- Recent Parking History -->
    <div class="card mb-4">
      <div class="card-header bg-primary text-white">
        Recent Parking History
      </div>
      <div class="card-body">
        <DataTable :columns="reservationColumns" :rows="reservations">
          <!-- Custom cell for From -->
          <template #start_time="{ row }">
            {{ f_date(row.start_time) }}
          </template>
          <!-- Custom cell for To -->
          <template #end_time="{ row }">
            {{ f_date(row.end_time) }}
          </template>
          <!-- Custom cell for Action -->
          <template #status="{ row }">
            <button v-if="row.status === 'active'" class="btn btn-sm btn-danger" @click="releaseSpot(row.id)">
              Release
            </button>
            <span v-else class="badge bg-success">Parked Out</span>
          </template>
        </DataTable>
      </div>
    </div>


  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import { useAuthStore} from "../stores/auth";
import * as bootstrap from "bootstrap";
import { apiFetch } from "@/api";
import apiClient from '@/apiClient';
import DataTable from "@/components/DataTable.vue";
import { useSearchStore } from "../stores/search";
import { storeToRefs } from "pinia";
const auth = useAuthStore();
const { isLoggedIn, isAdmin, userName, userId: uid, token } = storeToRefs(auth);
const searchStore = useSearchStore();

const reservationColumns = [
  { key: "lot_prefix", label: "ID", filterType: "select", type: "noedit" },
  { key: "spot_id", label: "Location", type: "noedit" },
  { key: "vehicle_number", label: "Vehicle No", type: "text" },
  { key: "start_time", label: "From", type: "text" },
  { key: "end_time", label: "To", type: "text" },
  { key: "driver_name", label: "Driver Name", type: "text" },
  { key: "driver_contact", label: "Driver Contact" },
  { key: "cost", label: "Fee", type: "number" },
  { key: "status", label: "Action" }
];


// State
const reservations = ref([]);
const pinCodes = ref([]);
const selectedPin = ref("");
const lots = ref([]);
const currentUser = JSON.parse(localStorage.getItem("current_user", '{"name": "User"}'));
const f_date = (raw) => raw;
// state for modal + form
const selectedLot = ref(null);
const bookingModal = ref(null);
const form = ref({
  vehicle_no: "",
  user_name: "",
  user_id: ""
});
// Open modal
function openBookingModal(lot) {
  selectedLot.value = lot;
  form.value = { vehicle_no: "", user_name: "", user_id: "" };

  const modalEl = document.getElementById("bookingModal");
  bookingModal.value = new bootstrap.Modal(modalEl);
  bookingModal.value.show();
}
function closeDropdown() {
  lots.value = [];
}
// Confirm booking
async function confirmBooking() {
  if (!selectedLot.value) return;
  form.value.user_name = currentUser.name;
  form.value.user_id = currentUser.id;
  const res = await apiFetch("/api/user/spots", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token.value}`
    },
    body: JSON.stringify({
      action: "book",
      lot_id: selectedLot.value.id,
      vehicle_no: form.value.vehicle_no,
      user_name: form.value.user_name,
      user_id: form.value.user_id,
      driver_contact: form.value.driver_contact,
      driver_name: form.value.driver_name
    })
  });

  if (res.ok) {
    alert("Slot booked successfully!");
    bookingModal.value.hide();
    fetchReservations(); // refresh reservations
    fetchLots(); // refresh list of lots
  } else {
    const errorData = await res.json();
    // console.log("Failed to book slot:", errorData);
    alert("Failed to book slot: " + errorData.error);
  }
  closeDropdown();
}

// Fetch recent reservations
async function fetchReservations() {
  searchStore.setOpCode(searchStore.searchType);
  reservations.value = await apiClient.post('/user/reservations', { user_id: currentUser.id, });

}

// Release a spot headers: { "Content-Type": "application/json" },
async function releaseSpot(reservationId) {
  const res = await apiFetch(`/api/user/spots`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token.value}` },
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

// Fetch pin codes
async function fetchPinCodes() {
  const res = await apiFetch("/api/user/pincodes", {
    headers: { Authorization: `Bearer ${token.value}` },
  });
  if (res.ok) {
    pinCodes.value = await res.json();
  }
}

// Fetch lots by pin code
async function fetchLots() {
  if (!selectedPin.value) return;
  const res = await apiFetch(`/api/user/lots?pin_code=${selectedPin.value}`, {
    headers: { Authorization: `Bearer ${token.value}` },
  });
  if (res.ok) {
    lots.value = await res.json();
  }
}



onMounted(() => {
  searchStore.setNavbarAction(fetchReservations);
  fetchReservations();
  fetchPinCodes();
});
</script>
