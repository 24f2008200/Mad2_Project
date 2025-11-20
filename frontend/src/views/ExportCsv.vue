<template>
  <div class="p-3">

    <button class="btn btn-primary" @click="startExport" :disabled="loading">
      {{ loading ? "Exporting..." : "Export CSV" }}
    </button>

    <div v-if="status" class="mt-3">
      <strong>Status:</strong> {{ status }}
    </div>

    <a v-if="downloadUrl" class="btn btn-success mt-3" :href="downloadUrl">
      Download CSV
    </a>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { apiFetch } from "@/api";

const status = ref(null)
const taskId = ref(null)
const downloadUrl = ref(null)
const loading = ref(false)

async function startExport() {
  loading.value = true
  status.value = "Starting export..."

  const res = await apiFetch("/api/user/export-csv", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${localStorage.getItem("token")}`,
      "Content-Type": "application/json",
    }
  })

  const data = await res.json()
  taskId.value = data.task_id
  status.value = "Processing…"

  pollStatus()
}

function pollStatus() {
  const interval = setInterval(async () => {
    const res = await apiFetch(`/api/user/export-status/${taskId.value}`, {
      headers: {
        "Authorization": `Bearer ${localStorage.getItem("token")}`
      }
    })

    const data = await res.json()
    status.value = data.status

    if (data.status === "completed") {
      clearInterval(interval)
      downloadUrl.value = data.download_url
      loading.value = false
    }
  }, 2000)
}
</script>
