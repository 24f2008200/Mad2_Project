<template>

  <GenericForm :row="editingRow" :title="title" :fields="formSchema" @save="updateUser" @cancel="closeModal" />

</template>

<script setup>
import { reactive, ref } from "vue";
import { apiFetch } from "@/api";
import GenericForm from "@/components/GenericForm.vue";
import { useToast } from "vue-toastification";
import { useRouter } from "vue-router";
const router = useRouter();

const toast = useToast();

//  Define the schema (macro)
const formSchema = [
  { key: 'name', label: 'Name', type: 'text' },
  { key: 'email', label: 'Email', type: 'email' ,required:true},
  { key: 'mobile', label: 'Mobile', type: 'tel' ,required:true},
  { key: 'address', label: 'Address', type: 'textarea' },
  { key: "receive_reminders", label: "Receive Reminders", type: "select", options: ["Yes", "No"] },
  { key: "reminder_time", label: "Reminder Time", type: "text" },
  { key: 'google_chat_hook', label: 'Google Chat Hook', type: 'url' },
  { key: 'password', label: 'Password', type: 'password' },
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
async function updateUser(form_data) {
  // if (!validateForm()) return;

  try {
    const res = await apiFetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form_data),
    });
    const data = await res.json();

    if (res.ok) {
      success.value = true;
      message.value = data.message || "Registration successful!";
      toast.success(message.value);
      Object.keys(form).forEach(k => (form[k] = ""));
      toast.success("Registration successful!");
      router.push("/api/login");
    } else {
      success.value = false;
      message.value = data.error || "Registration failed.";
      toast.error(message.value);
      // flash("Error: " + err.message, "danger");
      console.error("Registration error:", message.value);
    }
  } catch (err) {
    success.value = false;
    message.value = "Server error.";
    toast.error(message.value);
    // flash("Error: " + err.message, "danger");
    console.error("Registration error:", err);
  }
}
async function closeModal() {
   router.push("/api/login");    
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
