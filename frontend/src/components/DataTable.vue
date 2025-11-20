<template>
  <div>
    <table class="table table-striped align-middle text-center">
      <thead>
        <tr>
          <th v-for="col in columns" :key="col.key" class="px-2 py-2">
            {{ col.label }}
            <div v-if="enableFilters" class="filters">
              <!-- <div v-for="col in columns" :key="col.key" class="mb-2"> -->
              <!-- <label class="me-2">{{ col.label || col.key }}</label> -->

              <!-- Dropdown filter -->
              <select v-if="col.filterType === 'select'" v-model="filters[col.key]"
                class="form-select form-select-sm w-auto d-inline-block">
                <option value="">All</option>
                <option v-for="v in uniqueValues(col.key)" :key="v" :value="v">
                  {{ v }}
                </option>
              </select>

              <!-- Input filter -->
              <input v-else v-model="filters[col.key]" type="text"
                class="form-control form-control-sm w-auto d-inline-block"
                :placeholder="`Filter by ${col.label || col.key}`" />
              <!-- </div> -->
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in filteredRows" :key="row.id">
          <!-- <td v-for="col in columns" :key="col.key" class="px-2 py-1">
            <slot :name="col.key" :row="row">{{ row[col.key] }}</slot>
          </td> -->
          <td v-for="col in columns" :key="col.key" class="px-2 py-1">
            <template v-if="col.type === 'action'">
              <button class="btn btn-sm btn-primary me-1"
                @click="emit('action-click', { action: col.key, id: row.id, row })">
                {{ col.label }}
              </button>
            </template>
            <template v-else>
              <slot :name="col.key" :row="row">{{ row[col.key] }}</slot>
            </template>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
const emit = defineEmits(["action-click"])


const props = defineProps({
  columns: { type: Array, required: true },
  rows: { type: Array, required: true },
  enableFilters: { type: Boolean, default: true }
})
 

const filters = ref({})

// console.log("DataTable rows:", props.rows);

const filteredRows = computed(() => {
  return props.rows.filter(row =>
    Object.keys(filters.value).every(key => {
      const filter = String(filters.value[key])
      if (!filter) return true

      const col = props.columns.find(c => c.key === key)
      const rawValue = row[key]
      const value = String(rawValue || "").toLowerCase()

      if (col?.filterType === "select") {
        // exact match for dropdown
        return value === filter.toLowerCase()
      } else {
        // special case: '~' means "pick only None/empty"
        if (filter === "~") {
          return rawValue === null || rawValue === undefined || rawValue === ""
        }
        // substring match for free typing
        return value.includes(filter.toLowerCase())
      }
    })
  )
})



// helper 
function uniqueValues(key) {
  const rows = props.rows || []
  return [...new Set(rows.map(r => r[key]).filter(v => v !== null && v !== undefined && v !== ""))]
}
</script>
