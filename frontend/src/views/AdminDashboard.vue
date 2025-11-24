<template>
  <div class="container-fluid mt-4">
    <h2>Parking Lots</h2>

    <div class="row">
      <ParkingLotCard v-for="lot in lots" :key="lot.id" :lot="lot" @edit-lot="handleEditLot"
        @delete-lot="handleDeleteLot" @slot-click="showSlotDetails" />
    </div>
    <!-- Popup modal -->
    <SlotDetailModal :visible="isModalOpen" :slot="selectedSlot" :lot="selectedLot"
      @deleteSlot="handleDeleteSlot" @close="isModalOpen = false" />
    <!-- Add Lot Button -->
    <div class="text-center mt-4">
      <!-- <button class="btn btn-primary btn-lg" data-bs-toggle="modal" data-bs-target="#lotModal" @click="handleEditLot(null)">  -->
      <button class="btn btn-primary btn-lg" @click="handleEditLot(null)">
        + Add Lot
      </button>
    </div>

    <!-- Add/Edit Lot Modal --> 
    <div class="modal fade" id="lotModal" tabindex="-1" aria-labelledby="lotModalLabel" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="lotModalLabel">{{ isEdit ? "Edit Lot" : "Add New Lot" }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="updateLot">
              <div class="mb-3">
                <label class="form-label">Name</label>
                <input v-model="formLot.name" type="text" class="form-control" required />
              </div>
              <div class="mb-3">
                <label class="form-label">Prefix</label>
                <input v-model="formLot.prefix" type="text" class="form-control" required />
              </div>
              
              <div class="mb-3">
                <label class="form-label">Address</label>
                <input v-model="formLot.address" type="text" class="form-control" required />
              </div>
              <div class="mb-3">
                <label class="form-label">Pin Code</label>
                <input v-model="formLot.pin_code" type="text" class="form-control" required />
              </div>
              <div class="mb-3">
                <label class="form-label">Price (₹)</label>
                <input v-model.number="formLot.price" type="number" class="form-control" required />
              </div>
              <div class="mb-3">
                <label class="form-label">Number of Spots</label>
                <input v-model.number="formLot.number_of_spots" type="number" class="form-control" required />
              </div>
              <div class="d-flex justify-content-between">
                <button type="submit" class="btn btn-success">{{ isEdit ? "Update" : "Save" }}</button>
                <button type="button" class="btn btn-secondary me-2" @click="closeModalAndRefresh">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Modal } from 'bootstrap'
import apiClient from '@/apiClient';
import ParkingLotCard from '../components/ParkingLotCard.vue'
import SlotDetailModal from '../components/SlotDetailModal.vue'

// --------------------------------------------------
// Reactive State
// --------------------------------------------------
const lots = ref([])
const formLot = ref({ name: '', address: '', pin_code: '', price: null, number_of_spots: null })
const isEdit = ref(false)
const editId = ref(null)

const isModalOpen = ref(false)
const selectedSlot = ref({})
const selectedLot = ref(null)
const selectedReservation = ref(null)

// --------------------------------------------------
// Core CRUD Methods
// --------------------------------------------------
async function fetchLots() {
  // console.log('Fetching lots from API...')

  try {
    lots.value = await apiClient.get("/admin/lots", )
  } catch (err) {
    console.error('Error fetching lots:', err)
  }
}

function showSlotDetails(slot, lot) {
  selectedSlot.value = slot
  selectedLot.value = lot
  isModalOpen.value = true
}

function showModal() {
  const modalEl = document.getElementById('lotModal')
  const modal = Modal.getOrCreateInstance(modalEl)
  modal.show()
}

function openAddForm() {
  isEdit.value = false
  formLot.value = { name: '', address: '', pin_code: '', price: null, number_of_spots: null }
  nextTick(() => showModal())
}

function handleEditLot(lot) {
  if (!lot) {
    isEdit.value = false
    formLot.value = { name: '', address: '', pin_code: '', price: null, number_of_spots: null }
  } else {
    isEdit.value = true
    editId.value = lot.id
    formLot.value = { ...lot }
  }
  nextTick(() => showModal())
}

async function updateLot() {
  if (isEdit.value) {
    await apiClient.put(`/admin/lots/${editId.value}`, formLot.value)
    // await handleUpdates(`/api/admin/lots/${editId.value}`, 'PUT', formLot.value)
  } else {
    await apiClient.post('/admin/lots', formLot.value)
  }
  await closeModalAndRefresh()
}

async function handleDeleteLot(id) {
  if (!confirm('Are you sure you want to delete this lot?')) return
  console.log('Deleting lot with ID:', id)
  await apiClient.del(`/admin/lots/${id}`);
  await fetchLots();
}

async function handleDeleteSlot(slot) {
  if (!confirm('Are you sure you want to delete this slot?')) return
  isModalOpen.value = false
  await apiClient.del(`/admin/slots/${slot.id}`);
  await fetchLots();
}

async function handleUpdates(url, method, data) {
  const token = localStorage.getItem('access_token')
  try {

    const res = await apiClient(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: data ? JSON.stringify(data) : null,
    })
    if (res.ok) {
      await fetchLots()
    } else {
      console.error('Failed to perform operation')
    }
  } catch (err) {
    console.error('Error performing operation:', err)
  }
}

async function closeModalAndRefresh() {
  const modalEl = document.getElementById('lotModal')
  const modal = Modal.getInstance(modalEl)
  if (!modal) return

  modalEl.addEventListener(
    'hidden.bs.modal',
    async () => {
      await fetchLots()
      formLot.value = { name: '', address: '', pin_code: '', price: null, number_of_spots: null }
      editId.value = null
      isEdit.value = false
    },
    { once: true }
  )

  modal.hide()
}

// --------------------------------------------------
// Lifecycle Hook
// --------------------------------------------------
onMounted(fetchLots)
</script>
