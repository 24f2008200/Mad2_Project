
<template>
  <div class="card lot-list">
    <h3>Lots</h3>
    <div v-if="loading">Loading...</div>
    <div v-else>
      <div v-for="lot in lots" :key="lot.id" style="padding:6px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; align-items:center">
        <div>{{lot.name}} <small>({{lot.number_of_spots}})</small></div>
        <div><button @click="$emit('select', lot)">Open</button></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { toRefs } from 'vue'
const props = defineProps({ lots: Array, loading: Boolean })
const emit = defineEmits(['select'])
</script>
