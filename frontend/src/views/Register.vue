<template>
  <form @submit.prevent="handleRegister" class="container mt-5">
    <div class="card shadow-sm border-0 rounded-3 p-4 mx-auto" style="max-width: 650px;">
      <h4 class="mb-4 text-center text-primary">Register</h4>

      <div class="row mb-3 align-items-center">
        <div class="col-md-4 text-md-end">
          <label class="form-label mb-0">Name</label>
        </div>
        <div class="col-md-8">
          <input v-model="form.name" type="text" class="form-control" required />
        </div>
      </div>

      <div class="row mb-3 align-items-center">
        <div class="col-md-4 text-md-end">
          <label class="form-label mb-0">Email</label>
        </div>
        <div class="col-md-8">
          <input v-model="form.email" type="email" class="form-control" required />
        </div>
      </div>

      <div class="row mb-3 align-items-center">
        <div class="col-md-4 text-md-end">
          <label class="form-label mb-0">Mobile</label>
        </div>
        <div class="col-md-8">
          <input v-model="form.mobile" type="text" class="form-control" />
        </div>
      </div>
      <div class="row mb-3 align-items-center">
        <div class="col-md-4 text-md-end">
          <label class="form-label mb-0">Reminder ?</label>
        </div>
        <div class="col-md-8">
          <input v-model="form.r_reminder" type="checkbox" class="form-check-input" />
        </div>
      </div>
      <div class="row mb-3 align-items-center">
        <div class="col-md-4 text-md-end">
          <label class="form-label mb-0"> Reminder Time <Time></Time></label>
        </div>
        <div class="col-md-8">
          <input v-model="form.reminder_time" type="time" class="form-control" />
        </div>
      </div>

      <div class="row mb-3">
        <div class="col-md-4 text-md-end">
          <label class="form-label mb-0">Address</label>
        </div>
        <div class="col-md-8">
          <textarea v-model="form.address" class="form-control" rows="3"></textarea>
        </div>
      </div>

      <div class="row mb-3 align-items-center">
        <div class="col-md-4 text-md-end">
          <label class="form-label mb-0">Google Chat Hook</label>
        </div>
        <div class="col-md-8">
          <input
            v-model="form.google_chat_hook"
            type="url"
            class="form-control"
            placeholder="https://chat.googleapis.com/..."
          />
        </div>
      </div>

      <div class="row mb-3 align-items-center">
        <div class="col-md-4 text-md-end">
          <label class="form-label mb-0">Password</label>
        </div>
        <div class="col-md-8">
          <input v-model="form.password" type="password" class="form-control" required />
        </div>
      </div>

      <div class="row mb-3 align-items-center">
        <div class="col-md-4 text-md-end">
          <label class="form-label mb-0">Confirm Password</label>
        </div>
        <div class="col-md-8">
          <input
            v-model="form.confirm_password"
            type="password"
            class="form-control"
            :class="{ 'is-invalid': passwordMismatch }"
            required
          />
          <div class="invalid-feedback">Passwords do not match</div>
        </div>
      </div>

      <div class="text-center mt-4">
        <button type="submit" class="btn btn-primary px-4" :disabled="passwordMismatch">
          Register
        </button>
        <button type="button" class="btn btn-secondary px-4" @click="handleCancel">
          Cancel
        </button>
      </div>
    </div>
  </form>
</template>

<script setup>
import { reactive, ref, computed } from "vue";
import { apiFetch } from "@/api";
// import { useRouter } from "vue-router";
// const router = useRouter();
import { router } from "@/router";
const form = reactive({
  name: "",
  email: "",
  mobile: "",
  address: "",
  r_reminder: "",
  reminder_time: "",
  google_chat_hook: "",
  password: "",
  confirm_password: "",
});

const message = ref("");
const success = ref(false);

const passwordMismatch = computed(
  () => form.password && form.confirm_password && form.password !== form.confirm_password
);

function handleCancel() {
  Object.assign(form, {
    name: "",
    email: "",
    mobile: "",
    address: "",
    google_chat_hook: "",
    password: "",
    confirm_password: "",
  });
  message.value = "";
  success.value = false;
  router.push("/login");
}

async function handleRegister() {
  if (passwordMismatch.value) {
    message.value = "Passwords do not match!";
    success.value = false;
    return;
  }

  try {
    const response = await apiFetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: form.name,
        email: form.email,
        mobile: form.mobile,
        address: form.address,
        r_reminder: form.r_reminder,
        reminder_time: form.reminder_time,
        google_chat_hook: form.google_chat_hook,
        password: form.password,
      }),
    });

    const data = await response.json();

    if (response.ok) {
      success.value = true;
      message.value = data.message || "Registration successful!";
      Object.assign(form, {
        name: "",
        email: "",
        mobile: "",
        address: "",
        r_reminder: "",
        reminder_time: "",
        google_chat_hook: "",
        password: "",
        confirm_password: "",
      });
    } else {
      success.value = false;
      message.value = data.error || "Registration failed.";
    }
  } catch (err) {
    console.error("Error during registration:", err);
    success.value = false;
    message.value = "Server error. Please try again.";
  }
}
</script>



<style scoped>
/* Outer container gives breathing space */
.container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100vh;
  background: #f8f9fa; /* soft gray background */
  padding-top: 40px;
}

/* Card-like wrapper */
.card {
  width: 100%;
  max-width: 650px;
  background: #c1becd; /* #ffffff; */
  border: 1px solid #dee2e6;
  border-radius: 12px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08); /* gentle elevation */
  padding: 2rem;
  transition: all 0.2s ease-in-out;
}

/* Slight hover lift for elegance */
.card:hover {
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

/* Headings and labels */
.card h4 {
  font-weight: 600;
  text-align: center;
  color: #0d6efd;
  margin-bottom: 1.5rem;
}

.form-label {
  font-weight: 500;
  color: #495057;
}

/* Rounded, modern form controls */
.form-control {
  border-radius: 6px;
  border: 1px solid #ced4da;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-control:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.15rem rgba(13, 110, 253, 0.25);
}

/* Register button styling */
.btn-primary {
  border-radius: 25px;
  padding: 0.5rem 2rem;
  font-weight: 500;
}

/* Responsive alignment */
@media (max-width: 768px) {
  .text-md-end {
    text-align: left !important;
  }
  .card {
    padding: 1.5rem;
  }
}
</style>
