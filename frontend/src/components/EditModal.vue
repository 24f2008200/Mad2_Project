<template>
  <div class="modal fade" ref="modalEl">
    <div class="modal-dialog">
      <div class="modal-content p-3">
        <RowEditor :fields="fields" :row="row" @save="emitSave" @cancel="close" />
      </div>
    </div>
  </div>
</template>

<script setup>
import RowEditor from "./RowEditor.vue";
import { useModal } from "@/composables/useModal";

const props = defineProps({
  fields: Array,
  row: Object,
});

const emit = defineEmits(["save"]);

const { modalEl, open, close } = useModal();

function emitSave(updated) {
  emit("save", updated);
  close();
}

defineExpose({ open });
</script>
