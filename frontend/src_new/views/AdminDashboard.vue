
<template>
  <div class="container grid">
    <div>
      <LotList :lots="lots" :loading="loading" @select="onSelect"/>
      <AdminSearch />
    </div>
    <div>
      <div class="card">
        <h2 v-if="selectedLot">{{selectedLot.name}}</h2>
        <div v-else>Select a lot</div>
        <div v-if="selectedLot">
          <ParkingMap :lot="selectedLot" :period="period" :fetchDetails="fetchLotDetails" @spot-click="onSpotClick"/>
        </div>
      </div>
      <div class="card" v-if="spotInfo">
        <h4>Spot details</h4>
        <pre>{{JSON.stringify(spotInfo, null, 2)}}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, reactive } from 'vue'
import LotList from '../components/LotList.vue'
import ParkingMap from '../components/ParkingMap.vue'
import AdminSearch from '../components/AdminSearch.vue'
import { useAdmin } from '../composables/useAdmin'

const props = defineProps({ period: Object })
const { lots, loading, loadLots, loadLotDetails } = useAdmin()
const selectedLot = ref(null)
const spotInfo = ref(null)

onMounted(()=> loadLots())

function onSelect(lot){
  selectedLot.value = lot
  // do not load full spots until user clicks a spot (lightweight)
}

async function fetchLotDetails(lotId, opts={}){
  // proxy to composable
  return await loadLotDetails(lotId, opts)
}

function onSpotClick(info){
  // fetch detailed info for this spot on demand
  if(info && info.id){
    loadLotDetails(selectedLot.value.id, { spot_id: info.id }).then(res=>{
      // Expect response shape with spot details, otherwise fallback
      spotInfo.value = res.data?.spot || res.spot || info
    }).catch(e=>{ spotInfo.value = {error: e.message} })
  }
}
</script>
