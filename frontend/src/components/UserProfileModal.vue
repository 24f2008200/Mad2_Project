<template>
  <div class="modal fade" tabindex="-1" ref="modalEl">
    <div class="modal-dialog modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            {{ isSelf ? "My Profile" : `User: ${form.name || "..."}` }}
          </h5>
          <button type="button" class="btn-close" @click="close"></button>
        </div>

        <div class="modal-body">
          <div v-if="loading">Loading...</div>
          <div v-else>
            <!-- Tabs -->
            <ul class="nav nav-tabs mb-3" role="tablist">
              <li class="nav-item">
                <button
                  class="nav-link"
                  :class="{ active: activeTab==='profile' }"
                  @click="activeTab='profile'"
                >
                  Profile Info
                </button>
              </li> 
              <li class="nav-item">
                <button
                  class="nav-link"
                  :class="{ active: activeTab==='operations' }"
                  @click="activeTab='operations'"
                >
                  Operational Data
                </button>
              </li>
            </ul>

            <!-- Profile Info -->
            <div v-if="activeTab==='profile'">
              <form @submit.prevent="submit">
                <div class="row g-3">
                  <div class="col-md-6">
                    <label class="form-label">Name</label>
                    <input v-model="form.name" class="form-control" />

                    <label class="form-label mt-2">Email</label>
                    <input v-model="form.email" type="email" class="form-control" />

                    <label class="form-label mt-2">Address</label>
                    <input v-model="form.address" type="text" class="form-control" />

                    <label class="form-label mt-2">Phone</label>
                    <input v-model="form.mobile" class="form-control" />
                  </div>

                  <div class="col-md-6">
                    <label class="form-label">New Password (optional)</label>
                    <input v-model="form.password" type="password" class="form-control" />

                    <label class="form-label mt-2">Confirm Password</label>
                    <input v-model="form.confirm_password" type="password" class="form-control" />

                    <!-- Admin-only controls -->
                    <div v-if="currentUserIsAdmin" class="mt-3">
                      <div class="form-check">
                        <input v-model="form.is_admin" type="checkbox" id="adminChk" class="form-check-input" />
                        <label for="adminChk" class="form-check-label">Admin User</label>
                      </div>
                      <div class="form-check mt-2">
                        <input v-model="form.is_blocked" type="checkbox" id="blockChk" class="form-check-input" />
                        <label for="blockChk" class="form-check-label">Blocked</label>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="mt-3 text-end">
                  <button type="button" class="btn btn-secondary me-2" @click="close">Cancel</button>
                  <button type="submit" class="btn btn-primary" :disabled="saving">Save</button>
                </div>
              </form>
            </div>

            <!-- Operational Data -->
            <div v-if="activeTab==='operations'">
              <h6 class="border-bottom pb-1">User Activity</h6>
              <ul class="list-group">
                <li class="list-group-item d-flex justify-content-between">
                  <span>Total Reservations</span>
                  <span>{{ operational.reservation_count }}</span>
                </li>
                <li class="list-group-item d-flex justify-content-between">
                  <span>Active Reservation</span>
                  <span>{{ operational.active_reservation || "-" }}</span>
                </li>
                <li class="list-group-item d-flex justify-content-between">
                  <span>Last Login</span>
                  <span>{{ formatDate(operational.last_login) }}</span>
                </li>
                <li class="list-group-item d-flex justify-content-between">
                  <span>Status</span>
                  <span>
                    <span v-if="form.is_blocked" class="badge bg-danger">Blocked</span>
                    <span v-else class="badge bg-success">Active</span>
                  </span>
                </li>
              </ul>
            </div>

            <!-- Messages -->
            <div v-if="serverError" class="alert alert-danger mt-2">{{ serverError }}</div>
            <div v-if="successMsg" class="alert alert-success mt-2">{{ successMsg }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch, computed } from "vue";
import { apiFetch } from "@/api";
import { useAuth } from "../stores/auth";
const props = defineProps({
  userId: { type: Number, default: null }, // null = self
  show: { type: Boolean, default: false },
  currentUserIsAdmin: { type: Boolean, default: false } // logged-in user’s role
})
const emit = defineEmits(["updated", "closed"])

const isSelf = computed(() => props.userId === null)

const modalEl = ref(null)
let bsModal = null

const activeTab = ref("profile")

const loading = ref(false)
const saving = ref(false)
const serverError = ref("")
const successMsg = ref("")

const form = reactive({
  name: "",
  email: "",
  address: " ",
  mobile: "",
  password: "",
  confirm_password: "",
  is_admin: false,
  is_blocked: false
})

const operational = reactive({
  reservation_count: 0,
  active_reservation: null,
  last_login: null
})

// modal open/close
watch(
  () => props.show,
  (newVal) => {
    if (!bsModal) {
      bsModal = new bootstrap.Modal(modalEl.value)
    }
    if (newVal) {
      fetchUser()
      bsModal.show()
    } else {
      bsModal.hide()
    }
  }
)

function close() {
  if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur()
  }
  emit("closed")
}

function formatDate(val) {
  return val ? new Date(val).toLocaleString() : "-"
}

// API calls
async function fetchUser() {
  loading.value = true
  activeTab.value = "profile"
  serverError.value = ""
  try {
    const token = localStorage.getItem("access_token")
    const url = isSelf.value
      ? `/api/user/profile/${props.userId}`
      : `/api/user/profile/${props.userId}`
    const res = await apiFetch(url, {
        method: "GET",
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
    if (!res.ok) throw new Error("Failed to load user")
    const data = await res.json()

    form.name = data.name 
    form.email = data.email
    form.mobile = data.mobile
    form.address = data.address
    form.is_admin = data.is_admin
    form.is_blocked = data.is_blocked
    form.password = ""
    form.confirm_password = ""

    operational.reservation_count = data.reservation_count || 0
    operational.active_reservation = data.active_reservation || null
    operational.last_login = data.last_login || null
  } catch (e) {
    serverError.value = e.message
  } finally {
    loading.value = false
  }
}

async function submit() {
  saving.value = true
  serverError.value = ""
  successMsg.value = ""
  try {
    const token = localStorage.getItem("access_token")
    const url = isSelf.value
      ? `/api/user/profile/${props.userId}`
      : `/api/user/profile/${props.userId}`
    const res = await apiFetch(url, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify(form)
    })
    if (!res.ok) throw new Error("Failed to update profile")
    const data = await res.json()
    successMsg.value = "Profile updated."
    emit("updated", data)
  } catch (e) {
    serverError.value = e.message
  } finally {
    saving.value = false
  }
}
</script>
