// src/stores/csvExportStore.js
import { defineStore } from "pinia";
import { ref } from "vue";
import { startCSVExport, getExportStatus } from "@/services/CSVExportService.js";

export const useCSVExportStore = defineStore("csvExport", () => {

  const status = ref(null);
  const taskId = ref(null);
  const downloadUrl = ref(null);
  const loading = ref(false);
  let poller = null;

  async function startExport() {
    loading.value = true;
    status.value = "Starting export...";

    const data = await startCSVExport();
    taskId.value = data.task_id;
    status.value = "Processing…";
    console.log(data)
    // pollStatus(); 
  }

  function pollStatus() {
    poller = setInterval(async () => {
      const data = await getExportStatus(taskId.value);

      status.value = data.status;

      if (data.status === "completed") {
        downloadUrl.value = data.download_url;
        loading.value = false;
        clearInterval(poller);
      }
    }, 2000);
  }

  function clear() {
    status.value = null;
    taskId.value = null;
    downloadUrl.value = null;
    loading.value = false;
    if (poller) clearInterval(poller);
  }

  return {
    status,
    taskId,
    downloadUrl,
    loading,
    startExport,
    clear
  };
});
