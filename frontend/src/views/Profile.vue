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
import { useAuthStore} from "../stores/auth";
import { storeToRefs } from "pinia";
const auth = useAuthStore();
const { isLoggedIn, isAdmin, userName, userId: uid, token } = storeToRefs(auth);

const userId = ref();
const show = ref(false);
let currentUserIsAdmin = ref(false);



onMounted(() => {

  // const { isAdmin, userName, userId: uid } = useAuthStore()

  userId.value = parseInt(uid.value)
  currentUserIsAdmin.value = isAdmin.value
  show.value = true

})
</script>
