<template>
  <div class="container mt-4">
    <h2>Edit Profile</h2>
    <div>
      <UserProfileModal :userId="userId" :currentUserIsAdmin="currentUserIsAdmin" :show="show" @closed="show = false" />

    </div>
  </div>
</template>

<script setup>
import UserProfileModal from '../components/UserProfileModal.vue';
import { ref, onMounted } from "vue";
import { useAuth } from "../stores/auth";

const userId = ref();
const show = ref(false);
let currentUserIsAdmin = ref(false);



onMounted(() => {

  const { isAdmin, userName, userId: uid } = useAuth()

  userId.value = parseInt(uid.value)
  currentUserIsAdmin.value = isAdmin.value
  show.value = true

})
</script>
