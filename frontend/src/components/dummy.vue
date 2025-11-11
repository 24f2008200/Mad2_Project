<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Modal } from 'bootstrap'
import { apiFetch } from '@/api'
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
  const token = localStorage.getItem('access_token')
  try {
    const res = await apiFetch('/api/admin/lots', {
      headers: { Authorization: `Bearer ${token}` },
    })
    lots.value = await res.json()
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
    await handleUpdates(`/api/admin/lots/${editId.value}`, 'PUT', formLot.value)
  } else {
    await handleUpdates('/api/admin/lots', 'POST', formLot.value)
  }
  await closeModalAndRefresh()
}

async function handleDeleteLot(id) {
  if (!confirm('Are you sure you want to delete this lot?')) return
  await handleUpdates(`/api/admin/lots/${id}`, 'DELETE', null)
}

async function handleDeleteSlot(slot) {
  if (!confirm('Are you sure you want to delete this slot?')) return
  isModalOpen.value = false
  await handleUpdates(`/api/admin/slots/${slot.id}`, 'DELETE', null)
}

async function handleUpdates(url, method, data) {
  const token = localStorage.getItem('access_token')
  try {
    const res = await apiFetch(url, {
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

<template>
  <!-- You can keep your existing template section as-is -->
</template>
