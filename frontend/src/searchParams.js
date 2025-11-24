import { useSearchStore } from "@/stores/search";


export function getCommonParams() {
  const s = useSearchStore()

  return {
    searchType: s.searchType || null,
    searchBy: s.searchBy || null,
    searchValue: s.searchValue || null,
    startDate: s.startDate || null,
    endDate: s.endDate || null,
    opCode: s.opCode || null,
  }
}
