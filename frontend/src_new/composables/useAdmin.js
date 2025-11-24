
import { ref } from 'vue'
import * as adminApi from '../api/admin'

export function useAdmin() {
  const lots = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function loadLots() {
    loading.value = true
    error.value = null
    try {
      const res = await adminApi.fetchLotsSummary()
      lots.value = res.data || res
    } catch (e) {
      error.value = e
    } finally { loading.value = false }
  }

  async function loadLotDetails(lotId, opts={}){
    try {
      const res = await adminApi.fetchLotDetails(lotId, opts)
      return res.data || res
    } catch(e){ throw e }
  }

  return { lots, loading, error, loadLots, loadLotDetails }
}
