import { ref } from "vue";
import { useAuth } from "../stores/auth";
import * as bootstrap from "bootstrap";
import { apiFetch } from "../api";

const { token } = useAuth();

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

// Confirm booking
async function confirmBooking() {
  if (!selectedLot.value) return;

  const res = await apiFetch("/api/user/reservations", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token.value}`
    },
    body: JSON.stringify({
      lot_id: selectedLot.value.id,
      vehicle_no: form.value.vehicle_no,
      user_name: form.value.user_name,
      user_id: form.value.user_id
    })
  });

  if (res.ok) {
    alert("Slot booked successfully!");
    bookingModal.value.hide();
    fetchLots(); // refresh list of lots
  } else {
    alert("Failed to book slot");
  }
}
