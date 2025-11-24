
<template>
  <div class="card">
    <h3>{{lot.name}} — Spots</h3>
    <div v-if="loading">Loading spots...</div>
    <div v-else>
      <div style="display:flex; flex-wrap:wrap">
        <Spot v-for="(s,i) in spots" :key="s.id" :index="i+1" :status="s.status" :info="s" @click="onSpotClick"/>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import Spot from './Spot.vue'
const props = defineProps({ lot: Object, period: Object, fetchDetails: Function })
const spots = ref([])
const loading = ref(false)

watch(()=> props.lot, async (nl)=>{
  if(!nl) return
  loading.value = true
  // fetch lightweight spot summary per-lot - assume lot has 'spots' minimal or we request details
  if(nl.spots && nl.spots.length){ spots.value = nl.spots }
  else {
    const data = await props.fetchDetails(nl.id, { lightweight: true })
    spots.value = data.spots || []
  }
  loading.value = false
})

function onSpotClick(info){
  // On-demand fetch: emit event for parent to fetch full reservation/details for that spot
  // parent handles showing modal or fetching
  emit('spot-click', info)
}

const emit = defineEmits(['spot-click'])
</script>
