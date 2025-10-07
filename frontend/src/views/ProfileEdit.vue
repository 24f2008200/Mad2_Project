<template>
  <div class="container py-3">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h3>My Profile</h3>
      <div>
        <button v-if="!editing" class="btn btn-outline-primary btn-sm" @click="startEdit">
          Edit Profile
        </button>
        <button v-else class="btn btn-secondary btn-sm me-2" @click="cancelEdit">Cancel</button>
        <button v-else class="btn btn-success btn-sm" @click="submit" :disabled="saving">
          <span v-if="saving" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
          Save
        </button>
      </div>
    </div>

    <!-- View mode -->
    <div v-if="!editing" class="card p-3">
      <div class="row">
        <div class="col-md-6">
          <p><strong>Name:</strong> {{ profile.name }}</p>
          <p><strong>Email:</strong> {{ profile.email }}</p>
          <p><strong>Phone:</strong> {{ profile.phone || '-' }}</p>
        </div>
        <div class="col-md-6">
          <p><strong>Role:</strong> {{ profile.is_admin ? 'Admin' : 'User' }}</p>
          <p><strong>Joined:</strong> {{ formattedDate(profile.created_at) }}</p>
        </div>
      </div>
    </div>

    <!-- Edit mode -->
    <div v-else class="card p-3">
      <form @submit.prevent="submit" novalidate>
        <div class="row g-3">
          <!-- left column -->
          <div class="col-md-6">
            <div class="mb-2">
              <label class="form-label">Name</label>
              <input v-model="form.name" type="text" class="form-control" :class="{ 'is-invalid': errors.name }" />
              <div class="invalid-feedback" v-if="errors.name">{{ errors.name }}</div>
            </div>

            <div class="mb-2">
              <label class="form-label">Email</label>
              <input v-model="form.email" type="email" class="form-control" :class="{ 'is-invalid': errors.email }" />
              <div class="invalid-feedback" v-if="errors.email">{{ errors.email }}</div>
            </div>

            <div class="mb-2">
              <label class="form-label">Phone</label>
              <input v-model="form.phone" type="tel" class="form-control" :class="{ 'is-invalid': errors.phone }" />
              <div class="invalid-feedback" v-if="errors.phone">{{ errors.phone }}</div>
            </div>
          </div>

          <!-- right column -->
          <div class="col-md-6">
            <div class="mb-2">
              <label class="form-label">Change Password (optional)</label>
              <div class="input-group">
                <input
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  class="form-control"
                  placeholder="New password"
                  :class="{ 'is-invalid': errors.password }"
                />
                <button class="btn btn-outline-secondary" type="button" @click="toggleShowPassword">
                  <span v-if="showPassword">Hide</span><span v-else>Show</span>
                </button>
                <div class="invalid-feedback" v-if="errors.password">{{ errors.password }}</div>
              </div>
              <small class="form-text text-muted">Leave blank if you don't want to change password.</small>
            </div>

            <div class="mb-2">
              <label class="form-label">Confirm Password</label>
              <input
                v-model="form.confirm_password"
                :type="showPassword ? 'text' : 'password'"
                class="form-control"
                placeholder="Confirm new password"
                :class="{ 'is-invalid': errors.confirm_password }"
              />
              <div class="invalid-feedback" v-if="errors.confirm_password">{{ errors.confirm_password }}</div>
            </div>

            <div class="mb-2">
              <label class="form-label">Other info</label>
              <textarea v-model="form.notes" class="form-control" rows="3" placeholder="Profile notes"></textarea>
            </div>
          </div>
        </div>

        <div class="mt-3 d-flex justify-content-end">
          <button type="button" class="btn btn-secondary me-2" @click="cancelEdit" :disabled="saving">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="saving">
            <span v-if="saving" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
            Save changes
          </button>
        </div>

        <div v-if="serverError" class="alert alert-danger mt-3">{{ serverError }}</div>
        <div v-if="successMsg" class="alert alert-success mt-3">{{ successMsg }}</div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, computed } from 'vue'


/*
  ADJUST:
  - API endpoints below to match your backend e.g. /api/user/profile
  - Authorization header: this uses a token from localStorage; replace with your store access if needed.
*/

// --- state ---
const profile = reactive({
  id: null,
  name: '',
  email: '',
  phone: '',
  is_admin: false,
  created_at: null,
  notes: ''
})

const editing = ref(false)
const saving = ref(false)
const showPassword = ref(false)
const serverError = ref('')
const successMsg = ref('')

// form and validation errors
const form = reactive({
  name: '',
  email: '',
  phone: '',
  password: '',
  confirm_password: '',
  notes: ''
})

const errors = reactive({})

// --- helpers ---
function formattedDate(iso) {
  if (!iso) return '-'
  try {
    const d = new Date(iso)
    return d.toLocaleString() // uses user locale; change format if you want
  } catch {
    return iso
  }
}

// populate form from profile
function populateFormFromProfile() {
  form.name = profile.name || ''
  form.email = profile.email || ''
  form.phone = profile.phone || ''
  form.notes = profile.notes || ''
  form.password = ''
  form.confirm_password = ''
  Object.keys(errors).forEach(k => delete errors[k])
  serverError.value = ''
  successMsg.value = ''
}

function startEdit() {
  populateFormFromProfile()
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  populateFormFromProfile()
}

// simple client-side validation
function validate() {
  Object.keys(errors).forEach(k => delete errors[k])
  serverError.value = ''
  successMsg.value = ''

  if (!form.name?.trim()) errors.name = 'Name is required.'
  if (!form.email?.trim()) errors.email = 'Email is required.'
  else if (!/^\S+@\S+\.\S+$/.test(form.email)) errors.email = 'Enter a valid email.'

  // phone optional but if provided do basic check
  if (form.phone && !/^[\d+\-\s()]{6,20}$/.test(form.phone)) errors.phone = 'Enter a valid phone number.'

  // password validation only when either password field has content
  const pwProvided = !!form.password || !!form.confirm_password
  if (pwProvided) {
    if (!form.password || form.password.length < 6) errors.password = 'Password must be at least 6 characters.'
    if (form.password !== form.confirm_password) errors.confirm_password = "Passwords don't match."
  }

  return Object.keys(errors).length === 0
}

// build payload only with changed values (so we don't accidentally overwrite)
function buildPayload() {
  const payload = {}
  if (form.name !== profile.name) payload.name = form.name
  if (form.email !== profile.email) payload.email = form.email
  if (form.phone !== profile.phone) payload.phone = form.phone
  if (form.notes !== profile.notes) payload.notes = form.notes
  if (form.password) payload.password = form.password
  return payload
}

// --- API calls ---
async function fetchProfile() {
  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch('/api/user/profile', {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })

    if (!res.ok) throw new Error('Failed to load profile')

    const data = await res.json()
    Object.assign(profile, data)
  } catch (err) {
    console.error('fetchProfile error', err)
    serverError.value = err.message
  }
}

async function submit() {
  if (!validate()) return

  const payload = buildPayload()
  if (Object.keys(payload).length === 0) {
    successMsg.value = 'No changes to save.'
    return
  }

  saving.value = true
  serverError.value = ''
  successMsg.value = ''

  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch('/api/user/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify(payload)
    })

    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data.message || 'Failed to update profile')
    }

    const data = await res.json()
    Object.assign(profile, data)
    successMsg.value = 'Profile updated successfully.'
    editing.value = false
  } catch (err) {
    console.error('save profile error', err)
    serverError.value = err.message
  } finally {
    saving.value = false
    form.password = ''
    form.confirm_password = ''
  }
}
function toggleShowPassword() {
  showPassword.value = !showPassword.value
}

// --- lifecycle ---
onMounted(() => {
  fetchProfile()
})
</script>

<style scoped>
/* small tweaks */
.card { border-radius: 0.5rem; }
</style>
