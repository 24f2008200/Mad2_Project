<template>
  <form @submit.prevent="handleSubmit" class="container mt-5">
    <div class="card shadow-sm border-0 rounded-3 p-4 mx-auto" style="max-width: 650px;">
      <h4 class="mb-4 text-center text-primary">{{ title }}</h4>

      <template v-for="field in schema" :key="field.name">
        <div class="row mb-3 align-items-center">
          <div class="col-md-4 text-md-end">
            <label class="form-label mb-0">{{ field.label }}</label>
          </div>
          <div class="col-md-8">
            <!-- Render textarea or input dynamically -->
            <textarea
              v-if="field.type === 'textarea'"
              v-model="form[field.name]"
              class="form-control"
              :rows="field.rows || 3"
              :required="field.required"
              :placeholder="field.placeholder"
            ></textarea>

            <input
              v-else
              v-model="form[field.name]"
              :type="field.type"
              class="form-control"
              :required="field.required"
              :placeholder="field.placeholder"
              :class="{ 'is-invalid': errors[field.name] }"
            />

            <div class="invalid-feedback">{{ errors[field.name] }}</div>
          </div>
        </div>
      </template>

      <div class="text-center mt-4">
        <button type="submit" class="btn btn-primary px-4">Register</button>
      </div>

      <div v-if="message" :class="['mt-3 text-center', success ? 'text-success' : 'text-danger']">
        {{ message }}
      </div>
    </div>
  </form>
</template>

<script setup>
import { reactive, ref } from "vue";
import { apiFetch } from "@/api";

//  Define the schema (macro)
const formSchema = [
  { name: "name", label: "Name", type: "text", required: true },
  { name: "email", label: "Email", type: "email", required: true },
  {
    name: "mobile",
    label: "Mobile",
    type: "text",
    required: true,
    validate: (val) => {
      if (!val) return "Mobile number is required";
      if (!/^\d{10}$/.test(val)) return "Must be a 10-digit number";
      return true;
    },
  },
  { name: "address", label: "Address", type: "textarea" },
  {
    name: "google_chat_hook",
    label: "Google Chat Hook",
    type: "url",
    placeholder: "https://chat.googleapis.com/...",
  },
  { name: "password", label: "Password", type: "password", required: true },
  {
    name: "confirm_password",
    label: "Confirm Password",
    type: "password",
    required: true,
    validate: (val, form) => val === form.password || "Passwords do not match",
  },
];

//  State
const schema = formSchema;
const form = reactive(Object.fromEntries(schema.map(f => [f.name, ""])));
const errors = reactive({});
const message = ref("");
const success = ref(false);
const title = "Register";

//  Validation helper
function validateForm() {
  Object.keys(errors).forEach(k => (errors[k] = "")); // reset

  let valid = true;
  for (const field of schema) {
    const val = form[field.name];
    if (field.required && !val) {
      errors[field.name] = "Required";
      valid = false;
    } else if (field.validate) {
      const result = field.validate(val, form);
      if (result !== true) {
        errors[field.name] = result;
        valid = false;
      }
    }
  }
  return valid;
}

//  Submit
async function handleSubmit() {
  if (!validateForm()) return;

  try {
    const res = await apiFetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    const data = await res.json();

    if (res.ok) {
      success.value = true;
      message.value = data.message || "Registration successful!";
      Object.keys(form).forEach(k => (form[k] = ""));
    } else {
      success.value = false;
      message.value = data.error || "Registration failed.";
    }
  } catch (err) {
    success.value = false;
    message.value = "Server error.";
  }
}
</script>

<style scoped>
.container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100vh;
  background: #f8f9fa;
  padding-top: 40px;
}
.card {
  width: 100%;
  background: #ffffff;
  border: 1px solid #dee2e6;
  border-radius: 12px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
}
</style>
