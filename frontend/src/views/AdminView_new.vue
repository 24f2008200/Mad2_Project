<template>
  <div class="container mt-4">
    <h2>{{ pageTitle }} Search</h2>

    <DataTable
      v-if="activeColumns"
      :columns="activeColumns"
      :rows="results"
      @action-click="handleEdit"
    />

    <EditModal
      ref="editor"
      :fields="editorFields"
      :row="editingRow"
      @save="saveChanges"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useSearchStore } from "@/stores/search";
import { columnsMap } from "@/constants/columns";
import { useSearch } from "@/composables/useSearch";
import DataTable from "@/components/DataTable.vue";
import EditModal from "@/components/EditModal.vue";

const searchStore = useSearchStore();
const { results, search } = useSearch();

const activeColumns = computed(() => columnsMap[searchStore.searchType]);
const pageTitle = computed(() => searchStore.searchType.toUpperCase());

const editor = ref(null);
const editingRow = ref(null);
const editorFields = ref([]);

onMounted(() => {
  searchStore.setNavbarAction(runSearch);
  runSearch();
});

async function runSearch() {
  await search(
    searchStore.searchType,
    searchStore.searchBy,
    searchStore.searchValue
  );
}

function handleEdit({ row }) {
  editingRow.value = { ...row };
  editorFields.value = activeColumns.value;
  editor.value.open();
}

function saveChanges(updated) {
  const idx = results.value.findIndex(r => r.id === updated.id);
  if (idx >= 0) results.value[idx] = updated;
}
</script>
