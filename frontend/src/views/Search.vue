<template>
  <div v-if="resultData && resultData.length > 0" class="row justify-content-center mb-4">
    <div class="row justify-content-center mb-4">
      <div class="col-12 col-lg-10">
        <div class="table-responsive">abc
          <DataTable :columns="resultColumns" :rows="resultData" @action-click="handleAction" />
        </div>
      </div>
    </div>
  </div>

  <!-- <div>{{ resultData }}</div> -->
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { useAuthStore} from "../stores/auth";
import { watch } from "vue";
import { apiFetch } from "@/api";
import DataTable from "@/components/DataTable.vue";
import RowEditor from "@/components/RowEditor.vue";
import { useSearchStore } from "../stores/search";
import { storeToRefs } from "pinia";
const auth = useAuthStore();
const { isLoggedIn, isAdmin, userName, userId: uid, token } = storeToRefs(auth);

import { Pie, Bar, Line } from "vue-chartjs"
import { CategoryScale, LinearScale, BarElement, LineElement } from 'chart.js';

import { useRoute } from "vue-router"

const searchStore = useSearchStore();
const resultColumns = [
  { key: "table", label: "Table", filterType: "select", type: "noedit" },
  { key: "row_id", label: "Row No", type: "noedit" },
  { key: "column", label: "Column No", type: "text" },
  { key: "matched_value", label: "Matched Value", type: "text" },
  // { key: "end_time", label: "To" , type: "text" },
  // { key: "driver_name", label: "Driver Name" , type: "text" },
  // { key: "driver_contact", label: "Driver Contact" },
  //  { key: "status", label: "Action"  }
];


// ChartJS.register(Title, Tooltip, Legend, ArcElement, BarElement, LineElement, CategoryScale, LinearScale, PointElement)

const resultData = ref("")
const revenueData = ref(null)
const reservationData = ref(null)



const summary = ref({});



onMounted(async () => {
  searchStore.setFetchAction(fetchData);
  fetchData();
})

onUnmounted(() => {
  // Clean up when leaving page
  searchStore.setFetchAction(null)
})
// watch(
//   () => searchStore.value,
//   (newVal) => {
//     fetchData(newVal);
//   }
// );

async function fetchData() {
  const searchValue = searchStore.searchValue
  const searchBy = searchStore.searchBy
  const res = await apiFetch(`/api/admin/search?type=bquery&search_by=${searchBy}&value=${searchValue}`, {
    headers: { Authorization: `Bearer ${token.value}`, "Content-Type": "application/json" },
    method: "GET",
  });
  if (res.ok) {
    resultData.value = await res.json();
  }
}

function handleAction() { }
console.log("I am here")
const downloadReport = async () => {
  const canvases = document.querySelectorAll("canvas")
  const images = []

  canvases.forEach((c, idx) => {
    images.push({
      name: `chart_${idx + 1}`,
      data: c.toDataURL("image/png")  // Base64 PNG
    })
  })

  const response = await apiFetch("/api/admin/reports/pdf", {
    method: "POST",
    headers: { Authorization: `Bearer ${token.value}`, "Content-Type": "application/json" },
    body: JSON.stringify({ charts: images })
  })

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "Parking_Report.pdf"
  a.click()
  window.URL.revokeObjectURL(url)
}

</script>