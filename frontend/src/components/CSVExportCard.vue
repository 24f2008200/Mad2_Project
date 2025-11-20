<template>
  <div class="card shadow-sm mt-4">
    <div class="card-header bg-primary text-white">
      Export Parking History (CSV)
    </div>

    <div class="card-body">

      <button
        class="btn btn-primary"
        @click="exportStore.startExport"
        :disabled="exportStore.loading"
      >
        <span v-if="exportStore.loading">Generating...</span>
        <span v-else>Export CSV</span>
      </button>

      <div v-if="exportStore.status" class="mt-3">
        <strong>Status:</strong> {{ exportStore.status }}
      </div>

      <div v-if="exportStore.downloadUrl" class="mt-3">
        <a :href="exportStore.downloadUrl" class="btn btn-success">
          Download CSV
        </a>
      </div>

    </div>
  </div>
</template>

<script setup>
import { useCSVExportStore } from "@/stores/csvExportStore.js"

const exportStore = useCSVExportStore()
</script>
 