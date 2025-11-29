<template>
  hi reg vue
  <DynamicFormModal
    :show="show"
    title="Register"
    :schema="registerSchema"
    :fetchUrl="null" 
    :submitUrl="submitUrl"
    method="POST"
    modalSize="modal-lg"
    @saved="onSuccess"
    @closed="handleClose"
  />

  am i ok
</template>

<script setup>
import DynamicFormModal from "@/components/DynamicFormModal.vue";
import { registerSchema } from "@/schemas/registerSchema";
// import { useRouter } from "vue-router";
import { router } from "@/router";
import { useToast } from "vue-toastification";
const props = defineProps({
  userId: { type: Number, default: null },   // null = self
  show: Boolean
});

// const router = useRouter();
const toast = useToast();

const submitUrl = "/api/auth/register";
console.log("Register.vue loaded");
function onSuccess() {
  toast.success("Registration successful!");
  router.push("/login");
}
function handleClose() {
  router.push("/login");
}
</script>
