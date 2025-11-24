
<template>
  <div class="nav">
    <div>Parking Admin</div>
    <div style="display:flex; gap:10px; align-items:center">
      <select v-model="month"><option :value="null">All months</option><option v-for="(m,i) in months" :key="i" :value="i+1">{{m}}</option></select>
      <select v-model="year"><option :value="null">All years</option><option v-for="y in years" :key="y">{{y}}</option></select>
      <button @click="apply">Apply</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
const month = ref(null)
const year = ref(new Date().getFullYear())
const years = Array.from({length:5}).map((_,i)=> new Date().getFullYear()-i)

function apply(){ emit('changePeriod',{ month: month.value, year: year.value }) }

const emit = defineEmits(['changePeriod'])
</script>
