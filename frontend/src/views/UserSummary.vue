<template>
  <div class="container my-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2>User Dashboard</h2>
      <div>
        <select v-model="selectedYear" @change="fetchAll" class="form-select">
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>
    </div>

    <!-- Summary cards -->
    <div class="row g-3 mb-4">
      <div class="col-md-3" v-for="card in summaryCards" :key="card.title">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">{{ card.title }}</h6>
            <h3 class="card-title">{{ card.value }}</h3>
            <p class="card-text small text-muted">{{ card.hint }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-lg-8 mb-4">
        <div class="card h-100">
          <div class="card-header">Monthly Expenses ({{ selectedYear }})</div>
          <div class="card-body">
            <div style="height: 300px;">
              <canvas id="monthlyExpensesChart"></canvas>
            </div>

            <!-- <div class="mt-3 d-flex justify-content-end">
              <button class="btn btn-outline-secondary btn-sm me-2" @click="downloadCsv('monthly')">Export CSV</button>
              <button class="btn btn-primary btn-sm" @click="openDetails('monthly')">View details</button>
            </div> -->
          </div>
        </div>
      </div>

      <div class="col-lg-4 mb-4">
        <div class="card h-100">
          <div class="card-header">Location-wise Spend (Top locations)</div>
          <div class="card-body">
            <div style="height: 300px;">
              <canvas id="locationSpendChart"></canvas>
            </div>

            <ul class="list-group list-group-flush mt-3">
              <li class="list-group-item d-flex justify-content-between align-items-center" v-for="loc in topLocations"
                :key="loc.location">
                <div>
                  <div class="fw-semibold">{{ loc.location }}</div>
                  <div class="small text-muted">{{ loc.count }} reservations</div>
                </div>
                <div>
                  <div class="fw-bold">{{ formatCurrency(loc.amount) }}</div>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Other reports -->
    <div class="row">
      <div class="col-lg-6 mb-4">
        <div class="card h-100">
          <div class="card-header">Reservation Activity (last 6 months)</div>
          <div class="card-body">
            <div style="height: 300px;">
              <canvas id="activityChart"></canvas>
            </div>

          </div>
        </div>
      </div>

      <div class="col-lg-6 mb-4">
        <div class="card h-100">
          <div class="card-header">Recent Reservations</div>
          <div class="card-body p-0">
            <table class="table mb-0">
              <thead class="table-light">
                <tr>
                  <th>Lot</th>
                  <th>Spot</th>
                  <th>Date</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in recentReservations" :key="r.id">
                  <td>{{ r.lot }}</td>
                  <td>{{ r.spot || r.spot_id }}</td>
                  <td>{{ formatDate(r.start) }}</td>
                  <td>{{ formatCurrency(r.amount || r.fee || 0) }}</td>
                </tr>
                <tr v-if="recentReservations.length === 0">
                  <td colspan="4" class="text-center small text-muted p-3">No recent reservations</td>
                </tr>
                <!-- <tr>
                  <div class="container mt-4">
                    <CSVExportCard />
                  </div>

                </tr> -->
              </tbody>
            </table>
          </div>
          <div class="card-footer text-end">
            <button class="btn btn-sm btn-outline-primary" @click="openDetails('reservations')">View all</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal for details -->
    <div class="modal fade" id="detailsModal" tabindex="-1" aria-hidden="true" ref="detailsModalEl">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ modalTitle }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <pre class="small">{{ modalContent }}</pre>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import CSVExportCard from "@/components/CSVExportCard.vue"
import { ref, onMounted, computed } from 'vue'
// import { useRouter } from "vue-router";
import { useAuthStore} from "../stores/auth";
import { useSearchStore } from "../stores/search";
import { apiFetch } from "@/api";
import { watch } from "vue";
import UserProfileModal from '../components/UserProfileModal.vue';

import { CategoryScale, LinearScale, BarElement, LineElement } from 'chart.js';
import { storeToRefs } from "pinia";
const auth = useAuthStore();
const {token} = storeToRefs(auth);

const selectedYear = ref(new Date().getFullYear())
const years = ref([])
const summaryCards = ref([])
const monthlyData = ref({ labels: [], amounts: [] })
const locationData = ref({ labels: [], amounts: [] })
const activityData = ref({ labels: [], counts: [] })
const topLocations = ref([])
const recentReservations = ref([])
const modalTitle = ref('')
const modalContent = ref('')

const searchStore = useSearchStore()
// const { token } = useAuthStore();

let monthlyChart = null
let locationChart = null
let activityChart = null

function buildYears() {
  const thisYear = new Date().getFullYear()
  for (let y = thisYear; y >= thisYear - 4; y--) years.value.push(y)
}

function formatCurrency(v) {
  if (v == null) return '₹0'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(v)
}

function formatDate(s) {
  if (!s) return '-'
  const d = new Date(s)
  return d.toLocaleString('en-IN')
}

async function fetchAll() {
  try {
    const year = selectedYear.value
    const [summaryRes, monthlyRes, locationRes, activityRes, recentRes] = await Promise.all([
      fetchData(`/api/user/spots?view=summary&year=${year}`),
      fetchData(`/api/user/spots?view=monthly&year=${year}`),
      fetchData(`/api/user/spots?view=location&year=${year}`),
      fetchData(`/api/user/spots?view=activity&months=6`),
      fetchData(`/api/user/spots?view=recent`)
    ])
    console.log({ summaryRes, monthlyRes, locationRes, activityRes, recentRes });

    // summary cards
    const s = summaryRes || {}
    summaryCards.value = [
      { title: 'Yearly Spend', value: formatCurrency(s.total_spend || 0), hint: 'Total paid for parking this year' },
      { title: 'Avg / month', value: formatCurrency(s.avg_monthly || 0), hint: 'Average monthly spend' },
      { title: 'Reservations', value: s.total_reservations || 0, hint: 'Total reservations this year' },
      { title: 'Active Reservations', value: s.active || 0, hint: 'Monthly/season passes' }
    ]

    // monthly
    monthlyData.value = {
      labels: monthlyRes.months,   // <-- FIXED
      amounts: monthlyRes.amounts  // <-- correct
    }
    // monthlyData.value.labels = m.months
    // monthlyData.value.amounts = m.amounts

    // location

    locationData.value = {
      labels: locationRes.locations,   // <-- FIXED
      amounts: locationRes.amounts  // <-- correct
    }
    // topLocations.value = locationRes.top

    // activity
    activityData.value = {
      labels: activityRes.months,
      counts: activityRes.counts
    }
    console.log(recentRes.value)
    recentReservations.value = recentRes

    console.log(recentReservations.value)
    renderCharts()
  } catch (err) {
    console.error('failed to fetch reports', err)
    // fallback: empty data
  }
}
async function fetchData(url) {

  const res = await apiFetch(url, {
    headers: { Authorization: `Bearer ${token.value}`, "Content-Type": "application/json" },
    method: "GET",
  });
  if (res.ok) {
    const data = await res.json();
    // console.log(data)
    return data
  } else { throw new Error("Request failed") }
}

function renderCharts() {
  // destroy if exists
  if (monthlyChart) monthlyChart.destroy()
  if (locationChart) locationChart.destroy()
  if (activityChart) activityChart.destroy()

  const mCtx = document.getElementById('monthlyExpensesChart')
  if (mCtx) {
    monthlyChart = new Chart(mCtx, {
      type: 'bar',
      data: {
        labels: monthlyData.value.labels,
        datasets: [{ label: 'Amount', data: monthlyData.value.amounts }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    })

  }

  const lCtx = document.getElementById('locationSpendChart')
  if (lCtx) {
    locationChart = new Chart(lCtx, {
      type: 'doughnut',
      data: { labels: locationData.value.labels, datasets: [{ data: locationData.value.amounts }] },
      options: { responsive: true, maintainAspectRatio: false }
    })
  }

  const aCtx = document.getElementById('activityChart')
  if (aCtx) {
    activityChart = new Chart(aCtx, {
      type: 'line',
      data: { labels: activityData.value.labels, datasets: [{ label: 'Reservations', data: activityData.value.counts, fill: false, tension: 0.2 }] },
      options: { responsive: true, maintainAspectRatio: false }
    })
  }
}

function downloadCsv(kind) {
  // Build CSV client-side from currently loaded data
  let csv = ''
  if (kind === 'monthly') {
    csv += 'month,amount\n'
    monthlyData.value.labels.forEach((m, i) => {
      csv += `${m},${monthlyData.value.amounts[i] || 0}\n`
    })
  }
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `parking_${kind}_${selectedYear.value}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function openDetails(kind) {
  modalTitle.value = ({ monthly: 'Monthly details', reservations: 'All reservations' }[kind]) || 'Details'
  // For prototype, show JSON. In real app, you could fetch a paginated endpoint.
  if (kind === 'monthly') modalContent.value = JSON.stringify({ months: monthlyData.value.labels, amounts: monthlyData.value.amounts }, null, 2)
  else if (kind === 'reservations') modalContent.value = JSON.stringify(recentReservations.value, null, 2)
  else modalContent.value = 'No details'

  // show bootstrap modal
  const modalEl = document.getElementById('detailsModal')
  if (modalEl) {
    const bs = bootstrap.Modal.getOrCreateInstance(modalEl)
    bs.show()
  }
}

onMounted(async () => {
  buildYears()
  fetchAll()
})

</script>

<style scoped>
.card-header {
  font-weight: 600
}
</style>

<!--
Notes:

- Backend endpoints (suggested):
  
- Feel free to ask if you want this ported to use Vuex/Pinia state or to add filters (by lot, tag, subscription), or CSV/PDF export on server-side.
-->
