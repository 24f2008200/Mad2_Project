
<template>
  <div :class="['spot', statusClass]" :title="title" @click="onClick">
    <small>{{index}}</small>
  </div>
</template>

<script setup>
const props = defineProps({ index: Number, status: String, info: Object })
const emit = defineEmits(['click'])
const statusClass = computed(()=> props.status === 'O' ? 'occupied' : 'available')
const title = computed(()=> props.info?.vehicle_number ? props.info.vehicle_number : (props.status==='O' ? 'Occupied' : 'Available'))
function onClick(){ emit('click', props.info) }
</script>
