// src/services/CSVExportService.js
import { apiFetch } from "@/api";
import { useAuthStore} from "../stores/auth";

// const auth = useAuthStore();
// const { token } = storeToRefs(auth);

export async function startCSVExport() {
  const url = "/api/user/export-csv";
  const { token } = useAuthStore();
  const res = await apiFetch(url, {
    headers: { Authorization: `Bearer ${token.value}`, "Content-Type": "application/json" },
    method: "POST",
  });
  return res.json();
}

export async function getExportStatus(taskId) {
  const res = await apiFetch(`/api/user/export-status/${taskId}`, {
    headers: {
      "Authorization": `Bearer ${localStorage.getItem("token")}`
    }
  });
  return res.json();
}
