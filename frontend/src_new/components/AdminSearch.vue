
<template>
  <div class="card">
    <h3>Admin Search</h3>
    <div style="display:flex;gap:6px">
      <select v-model="type"><option value="users">Users</option><option value="bookings">Bookings</option><option value="lots">Lots</option></select>
      <input v-model="value" placeholder="search"/>
      <button @click="doSearch">Search</button>
    </div>
    <div v-if="loading">Searching...</div>
    <div v-else>
      <pre style="white-space:pre-wrap">{{JSON.stringify(result, null, 2)}}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchAll } from '../api/admin'
const type = ref('users'), value = ref('')
const loading = ref(false), result = ref(null)

async function doSearch(){
  loading.value = true
  try{
    const res = await searchAll(type.value, '', value.value)
    result.value = res.data || res
  }catch(e){ result.value = {error: e.message} }
  finally{ loading.value = false }
}
</script>
