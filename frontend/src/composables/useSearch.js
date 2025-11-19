import { ref } from "vue";
import { apiFetch } from "@/api";
import { useSearchEndpoint } from "./useSearchEndpoint";

export function useSearch() {
  const results = ref([]);
  const loading = ref(false);

  const { buildEndpoint } = useSearchEndpoint();

  async function search(type, by, value) {
    loading.value = true;

    try {
      const url = buildEndpoint(type, by, value);
      const res = await apiFetch(url, {
        headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
      });

      results.value = await res.json();
    } finally {
      loading.value = false;
    }
  }

  return { results, loading, search };
}
