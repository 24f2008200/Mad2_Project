<template>
  <div class="container-fluid mt-4">
    <h2>Summary Reports</h2>

    <div class="row text-center mb-4">
      <div class="col">
        <h5>Total Users</h5>
        <p>{{ summary.total_users }}</p>
      </div>
      <div class="col">
        <h5>Active Reservations</h5>
        <p>{{ summary.active_reservations }}</p>
      </div>
      <div class="col">
        <h5>Parking Lots</h5>
        <p>{{ summary.lots }}</p>
      </div>
    </div>

    <!-- Removed LineChart for now -->
  </div>

  <div class="container mt-4">
    <h3>Admin Reports</h3>

    <button @click="downloadReport" class="btn btn-primary mb-3">
      Download Report as PDF
    </button>

    <div class="row">
      <div class="col-md-6">
        <h5>Lot-wise Occupancy</h5>
        <Bar v-if="occupancyData" :data="occupancyData" />
      </div>

      <div class="col-md-6">
        <h5>Revenue Trend (Monthly)</h5>
        <Line v-if="revenueData" :data="revenueData" />
      </div>
    </div>

    <div class="row mt-4">
      <div class="col-md-12">
        <h5>Reservation Activity</h5>
        <Bar v-if="reservationData" :data="reservationData" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import apiClient from "@/apiClient"
import { useSearchStore } from "../stores/search"

// Vue-ChartJS + Chart.js (correct setup)
import { Bar, Line } from "vue-chartjs"

import { CategoryScale, LinearScale, BarElement, LineElement } from 'chart.js';

const searchStore = useSearchStore()
const summary = ref({})

const occupancyData = ref(null)
const revenueData = ref(null)
const reservationData = ref(null)

onMounted(async () => {
  // SUMMARY
  searchStore.setOpCode("summary")
  summary.value = await apiClient.post("/admin/reports")

  // OCCUPANCY
  searchStore.setOpCode("occupancy")
  const occRes = await apiClient.post("/admin/reports")

  occupancyData.value = {
    labels: occRes.map((l) => l.lot),
    datasets: [
      {
        label: "Available",
        data: occRes.map((l) => l.available),
        backgroundColor: "rgba(75,192,192,0.6)",
      },
      {
        label: "Occupied",
        data: occRes.map((l) => l.occupied),
        backgroundColor: "rgba(255,99,132,0.6)",
      },
    ],
  }

  // REVENUE TREND
  searchStore.setOpCode("revenue")
  const revRes = await apiClient.post("/admin/reports")

  const start = revRes.range.start
  const end = revRes.range.end
  const months = Array.from({ length: end - start + 1 }, (_, i) => start + i)

  const monthNames = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
  ]
  const labels = months.map((m) => monthNames[m - 1])

  revenueData.value = {
    labels,
    datasets: Object.keys(revRes.data).map((lot, idx) => ({
      label: lot,
      data: months.map((m) => revRes.data[lot][m] || 0),
      borderColor: `hsl(${idx * 70}, 70%, 50%)`,
      fill: false,
    })),
  }

  // RESERVATIONS PER LOT
  searchStore.setOpCode("reservations_by_lot")
  const resRes = await apiClient.post("/admin/reports")

  reservationData.value = {
    labels: resRes.map((r) => r.lot),
    datasets: [
      {
        label: "Bookings",
        data: resRes.map((r) => r.bookings),
        backgroundColor: "rgba(54,162,235,0.6)",
      },
    ],
  }
})

/* ---------------- PDF Download ---------------- */
const downloadReport = async () => {
  const canvases = document.querySelectorAll("canvas")
  const images = []

  canvases.forEach((c, idx) => {
    images.push({
      name: `chart_${idx + 1}`,
      data: c.toDataURL("image/png"),
    })
  })
  console.log("First Chart Base64: ", images[0].data.substring(0, 40));
  const data  =JSON.stringify({ charts: images });
  const blob = await apiClient.post("/admin/reports/pdf", data, {
    headers: { "Content-Type": "application/json" },
    responseType: "blob",
  });

const url = window.URL.createObjectURL(blob);
const a = document.createElement("a");
a.href = url;
a.download = "Parking_Report.pdf";

document.body.appendChild(a);
a.click();
document.body.removeChild(a);
window.URL.revokeObjectURL(url);

}
</script>
