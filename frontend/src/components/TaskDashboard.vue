<template>
  <div class="container py-4">

    <!-- Filters -->
    <div class="card mb-3">
      <div class="card-body d-flex flex-wrap gap-3 align-items-end">

        <div>
          <label>Status</label>
          <select v-model="filters.status" class="form-control" @change="fetchTasks">
            <option value="">All</option>
            <option>SUCCESS</option>
            <option>FAILED</option>
            <option>RUNNING</option>
            <option>PENDING</option>
          </select>
        </div>

        <div>
          <label>Worker</label>
          <select v-model="filters.worker" class="form-control" @change="fetchTasks">
            <option value="">All</option>
            <option v-for="w in workerList" :key="w">{{ w }}</option>
          </select>
        </div>

      </div>
    </div>

    <!-- Metrics -->
    <div class="row mb-3">

      <!-- Worker Health -->
      <div class="col-md-3" v-for="(state, worker) in metrics.workers" :key="worker">
        <div class="card p-3 text-center">
          <h6>{{ worker }}</h6>
          <span :class="['badge', state === 'online' ? 'badge bg-success' : 'badge bg-danger']">
            {{ state }}
          </span>
        </div>
      </div>

      <!-- Queue Length -->
      <div class="col-md-3">
        <div class="card p-3 text-center">
          <h6>Queue Length</h6>
          <h4>{{ metrics.queue_length }}</h4>
        </div>
      </div>

      <!-- Avg Duration -->
      <div class="col-md-3">
        <div class="card p-3 text-center">
          <h6>Avg Task Duration</h6>
          <h4>{{ metrics.avg_task_duration }}s</h4>
        </div>
      </div>

      <!-- Success Rate -->
      <div class="col-md-3">
        <div class="card p-3 text-center">
          <h6>Success Rate</h6>
          <h4>{{ (metrics.success_rate * 100).toFixed(1) }}%</h4>
        </div>
      </div>

    </div>

    <!-- Task Table -->
    <div class="card">
      <div class="card-body p-0">

        <table class="table mb-0">
          <thead class="thead-light">
            <tr>
              <th>Task</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Progress</th>
              <th>Worker</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="t in tasks" :key="t.id">
              <td>{{ t.name }}</td>

              <td>
                <span :class="statusClass(t.status)">
                  {{ t.status }}
                </span>
              </td>

              <td>{{ t.duration }}s</td>

              <td style="width: 200px">
                <div class="progress">
                  <div class="progress-bar"
                       role="progressbar"
                       :style="{ width: t.progress + '%' }">
                  </div>
                </div>
              </td>

              <td>{{ t.worker }}</td>
            </tr>
          </tbody>

        </table>

      </div>
    </div>

  </div>
</template>


<script setup>
import { ref, onMounted } from "vue";

const tasks = ref([]);
const metrics = ref({
  workers: {},
  queue_length: 0,
  avg_task_duration: 0,
  success_rate: 0
});

const workerList = ref([]);

const filters = ref({
  status: "",
  worker: ""
});

async function fetchMetrics() {
  const res = await fetch("/api/metrics");
  const json = await res.json();
  metrics.value = json;
  workerList.value = Object.keys(json.workers);
}

async function fetchTasks() {
  const params = new URLSearchParams(filters.value).toString();
  const res = await fetch(`/api/tasks?${params}`);
  const json = await res.json();
  tasks.value = json.tasks;
}

function statusClass(status) {
  return {
    SUCCESS: "badge bg-success",
    FAILED: "badge bg-danger",
    RUNNING: "badge bg-warning text-dark",
    PENDING: "badge bg-secondary"
  }[status] || "badge bg-light";
}

onMounted(() => {
  fetchMetrics();
  fetchTasks();

  // Auto-refresh every 5 seconds
  setInterval(() => {
    fetchMetrics();
    fetchTasks();
  }, 5000);
});
</script>
