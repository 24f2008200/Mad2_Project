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

    <h4>Revenue Chart</h4>
    <LineChart v-if="summary.revenue" :data="summary.revenue" />
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
import { ref, onMounted } from "vue";
import { useAuth } from "../stores/auth";
import LineChart from "../components/LineChart.vue";
import { apiFetch } from "@/api";

import { Chart as ChartJS, Title, Tooltip, Legend, ArcElement, BarElement, LineElement, CategoryScale, LinearScale, PointElement } from "chart.js"
import { Pie, Bar, Line } from "vue-chartjs"

ChartJS.register(Title, Tooltip, Legend, ArcElement, BarElement, LineElement, CategoryScale, LinearScale, PointElement)

const occupancyData = ref(null)
const revenueData = ref(null)
const reservationData = ref(null)


const { token } = useAuth();
const summary = ref({});


onMounted(async () => {
  // Lot-wise occupancy
  const occRes = await apiFetch("/api/admin/reports/occupancy", {
    headers: { Authorization: `Bearer ${token.value}` }
  }).then(r => r.json())
  occupancyData.value = {
    labels: occRes.map(l => l.lot),
    datasets: [
      {
        label: "Available",
        data: occRes.map(l => l.available),
        backgroundColor: "rgba(75,192,192,0.6)"
      },
      {
        label: "Occupied",
        data: occRes.map(l => l.occupied),
        backgroundColor: "rgba(255,99,132,0.6)"
      }
    ]
  }

  // Revenue trend (per lot per month)
  // const revRes = await apiFetch("/api/admin/reports/revenue",{
  //   headers: { Authorization: `Bearer ${token.value}` }
  // }).then(r => r.json())
  // const months = Array.from({ length: 12 }, (_, i) => i + 1)
  // revenueData.value = {
  //   labels: months,
  //   datasets: Object.keys(revRes).map((lot, idx) => ({
  //     label: lot,
  //     data: months.map(m => revRes[lot][m] || 0),
  //     borderColor: `hsl(${idx * 70}, 70%, 50%)`,
  //     fill: false
  //   }))
  // }
  const revRes = await apiFetch("/api/admin/reports/revenue", {
    headers: { Authorization: `Bearer ${token.value}` }
  }).then(r => r.json())

  // Month names (short form, you can use full names too)
  const monthNames = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
  ]

  // Get active range from backend
  const start = revRes.range.start
  const end = revRes.range.end

  // Build months dynamically
  const months = Array.from({ length: end - start + 1 }, (_, i) => start + i)

  // Convert to labels with names
  const labels = months.map(m => monthNames[m - 1])

  // Prepare chart datasets
  revenueData.value = {
    labels,
    datasets: Object.keys(revRes.data).map((lot, idx) => ({
      label: lot,
      data: months.map(m => revRes.data[lot][m] || 0),
      borderColor: `hsl(${idx * 70}, 70%, 50%)`,
      fill: false
    }))
  }

  // Reservation activity
  const resRes = await apiFetch("/api/admin/reports/reservations", {
    headers: { Authorization: `Bearer ${token.value}` }
  }).then(r => r.json())
  reservationData.value = {
    labels: resRes.map(r => r.lot),
    datasets: [
      {
        label: "Bookings",
        data: resRes.map(r => r.bookings),
        backgroundColor: "rgba(54,162,235,0.6)"
      }
    ]
  }
  const res = await apiFetch("/api/admin/summary", {
    headers: { Authorization: `Bearer ${token.value}` }
  });
  if (res.ok) {
    summary.value = await res.json();
  }

})

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
