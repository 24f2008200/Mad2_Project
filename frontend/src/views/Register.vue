<template>
  <div class="container mt-5" style="max-width: 500px;">
    <h2 class="mb-4">User Registration</h2>

    <form @submit.prevent="handleRegister">
      <div class="mb-3">
        <label class="form-label">Name</label>
        <input v-model="form.name" type="text" class="form-control" required />
      </div>

      <div class="mb-3">
        <label class="form-label">Email</label>
        <input v-model="form.email" type="email" class="form-control" required />
      </div>

      <div class="mb-3">
        <label class="form-label">Mobile</label>
        <input v-model="form.mobile" type="text" class="form-control" />
      </div>

      <div class="mb-3">
        <label class="form-label">Address</label>
        <input v-model="form.address" type="text" class="form-control" />
      </div>

      <div class="mb-3">
        <label class="form-label">Password</label>
        <input v-model="form.password" type="password" class="form-control" required />
      </div>

      <button type="submit" class="btn btn-primary w-100">Register</button>
    </form>

    <!-- Success / Error messages -->
    <div v-if="message" class="alert mt-3"
         :class="{'alert-success': success, 'alert-danger': !success}">
      {{ message }}
    </div>
  </div>
</template>

<script>
import { apiFetch } from "@/api";
export default {
  name: "Register",
  data() {
    return {
      form: {
        name: "",
        email: "",
        mobile: "",
        address: "",
        password: ""
      },
      message: "",
      success: false
    }
  },
  methods: {
    async handleRegister() {
      try {
        const response = await apiFetch("/api/user/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(this.form)
        })

        const data = await response.json()

        if (response.ok) {
          this.success = true
          this.message = data.message || "Registration successful!"
          this.form = { name: "", email: "", mobile: "", address: "", password: "" }
        } else {
          this.success = false
          this.message = data.error || "Registration failed"
        }
      } catch (err) {
        console.error("Error during registration:", err)
        this.success = false
        this.message = "Server error. Please try again."
      }
    }
  }
}
</script>
