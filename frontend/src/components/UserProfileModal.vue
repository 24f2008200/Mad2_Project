<template>
  <DynamicFormModal
    :show="show"
    title="User Profile"
    :schema="profileSchema"
    :fetchUrl="fetchUrl"
    :submitUrl="submitUrl"
    method="PUT"
    modalSize="modal-xl"
    :context="{ isAdmin: currentUserIsAdmin }"
    @closed="handleClose"
    @saved="handleSaved"
  />
</template>

<script setup>
import { computed } from "vue";
import DynamicFormModal from "@/components/DynamicFormModal.vue";
import { profileSchema } from "@/schemas/profileSchema";
import { useAuthStore} from "@/stores/auth";

const props = defineProps({
  userId: { type: Number, default: null },   // null = self
  show: Boolean
});

const emit = defineEmits(["closed", "updated"]);

const auth = useAuthStore();
const currentUserIsAdmin = computed(() => auth.isAdmin);

// ⭐ FIX: use your original backend structure
const fetchUrl = computed(() =>
  `/api/user/profile/${props.userId}`
);

const submitUrl = computed(() =>
  `/api/user/profile/${props.userId}`
);

function handleClose() {
  emit("closed");
}

function handleSaved(data) {
  emit("updated", data);
}
</script>
