<template>
  <div class="container mt-4">

    <div class="d-flex justify-content-between align-items-center mb-3">
      <h3>Celery Task Dashboard</h3>

      <div>
        <button class="btn btn-success me-2" @click="runTask">Run Task</button>
        <button class="btn btn-primary" @click="fetchTasks">Refresh</button>
      </div>
    </div>

    <input
      type="text"
      v-model="search"
      placeholder="Search tasks..."
      class="form-control mb-3"
    />

    <table class="table table-bordered table-striped">
      <thead>
        <tr>
          <th>ID</th>
          <th>Status</th>
          <th>Result</th>
          <th>Time</th>
          <th>Actions</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="t in filteredTasks" :key="t.id">
          <td>{{ t.id }}</td>
          <td>
            <span :class="statusClass(t.status)">
              {{ t.status }}
            </span>
          </td>
          <td>{{ t.result || "-" }}</td>
          <td>
            <div v-if="t.start_time">
              <div>Started: {{ formatDate(t.start_time) }}</div>
              <div v-if="t.end_time">Ended: {{ formatDate(t.end_time) }}</div>
              <div v-if="t.duration != null">Duration: {{ t.duration }}s</div>
            </div>
            <span v-else>-</span>
          </td>

          <td>
            <button
              class="btn btn-sm btn-outline-danger"
              @click="deleteTask(t.id)"
            >
              Delete
            </button>
          </td>
        </tr>

        <tr v-if="filteredTasks.length === 0">
          <td colspan="5" class="text-center py-3">No tasks found.</td>
        </tr>

      </tbody>
    </table>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import apiClient from '@/apiClient';

const tasks = ref([]);
const search = ref("");

async function fetchTasks() {
  try {
    const res = await apiClient.get("/tasks");
    tasks.value = res.data.tasks || [];
  } catch (err) {
    console.error("Failed to load tasks", err);
  }
}

async function runTask() {
  try {
    await apiClient.post("/run-task");
    fetchTasks();
  } catch (err) {
    console.error("Failed to run task", err);
  }
}

async function deleteTask(id) {
  try {
    await apiClient.delete(`/tasks/${id}`);
    fetchTasks();
  } catch (err) {
    console.error("Delete failed", err);
  }
}

const filteredTasks = computed(() => {
  if (!search.value.trim()) return tasks.value;

  return tasks.value.filter((t) =>
    JSON.stringify(t).toLowerCase().includes(search.value.toLowerCase())
  );
});

function formatDate(s) {
  return new Date(s).toLocaleString();
}

function statusClass(status) {
  return {
    "badge bg-secondary": status === "PENDING",
    "badge bg-info text-dark": status === "RUNNING",
    "badge bg-success": status === "SUCCESS",
    "badge bg-danger": status === "FAILED",
    "badge bg-warning text-dark": status === "REVOKED",
  };
}

onMounted(fetchTasks);
</script>

<style scoped>
.table td {
  vertical-align: middle;
}
</style>
