// src/services/CSVExportService.js
import { apiFetch } from "@/api";
import { useAuth } from "../stores/auth";
export async function startCSVExport() {
  const url = "/api/user/export-csv";
  const { token } = useAuth();
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
