
<template>
  <div id="app">
    <NavBar @changePeriod="onPeriodChange" />
    <router-view :period="period" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import NavBar from './components/NavBar.vue'

const period = ref({ month: null, year: null })

function onPeriodChange(p) {
  period.value = p
}
</script>
