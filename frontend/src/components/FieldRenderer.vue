<template>
  <div class="row mb-2 align-items-center">

    <!-- LABEL (except checkbox) -->
    <label v-if="field.type !== 'checkbox'" class="col-md-4 col-sm-12 form-label fw-semibold">
      {{ field.label }}
    </label>

    <!-- VALUE COLUMN -->
    <div :class="field.type === 'checkbox' ? 'col-12' : 'col-md-8 col-sm-12'">

      <!-- TEXT / EMAIL / PASSWORD / NUMBER -->
      <input v-if="['text', 'email', 'password', 'number'].includes(field.type)" :type="field.type" class="form-control"
        :value="modelValue" @input="emit('update:modelValue', $event.target.value)" />
      <!-- TIME -->
      <input v-else-if="field.type === 'time'" type="time" class="form-control" :value="modelValue"
        @input="emit('update:modelValue', $event.target.value)" />

      <!-- TEXTAREA -->
      <textarea v-else-if="field.type === 'textarea'" class="form-control" rows="3" :value="modelValue"
        @input="emit('update:modelValue', $event.target.value)"></textarea>

      <!--Password -->
      <input v-else-if="field.type === 'password'" type="password" class="form-control" :value="modelValue"
        @input="emit('update:modelValue', $event.target.value)" />
      <!-- PASSWORD-GROUP -->
      <div v-else-if="field.type === 'password-group'">

        <input type="password" class="form-control mb-2" placeholder="New Password" :value="modelValue.password || ''"
          @input="updatePassword('password', $event.target.value)" />

        <input type="password" class="form-control" placeholder="Confirm Password" :value="modelValue.confirm || ''"
          @input="updatePassword('confirm', $event.target.value)" />

      </div>

      <!-- SELECT -->
      <select v-else-if="field.type === 'select'" class="form-select" :value="modelValue"
        @change="emit('update:modelValue', $event.target.value)">
        <option v-for="opt in field.options" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>

      <!-- CHECKBOX (special layout) -->
      <div v-else-if="field.type === 'checkbox'" class="form-check">
        <label class="form-check-label">{{ field.label }}</label>
        <input type="checkbox" class="form-check-input" :checked="modelValue"
          @change="emit('update:modelValue', $event.target.checked)" />

      </div>

      <!-- ERRORS -->
      <div v-if="errors.length" class="text-danger small mt-1">
        <div v-for="err in errors" :key="err">{{ err }}</div>
      </div>

    </div>

  </div>
</template>


<script setup>
const props = defineProps({
  field: Object,
  modelValue: [String, Number, Boolean, Object],
  errors: { type: Array, default: () => [] }
});

const emit = defineEmits(["update:modelValue"]);

function updatePassword(key, value) {
  emit("update:modelValue", {
    ...props.modelValue,
    [key]: value
  });
}

</script>
