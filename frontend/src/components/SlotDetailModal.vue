<template>
  <div class="modal fade show" tabindex="-1" role="dialog" style="display: block; background: rgba(0,0,0,0.5);"
    v-if="visible">
    <div class="modal-dialog" role="document">
      <div class="modal-content">

        <div class="modal-header">
          <h5 class="modal-title" :class="slot.status == 'O' ? 'text-danger' : 'text-success'">
            {{ slot.status == 'O' ? 'Occupied Details' : 'Available / Delete' }}
          </h5>

          <button type="button" class="btn-close" @click="$emit('close')"></button>
        </div>

        <div class="modal-body">
          <p><strong>ID:</strong> {{ slot.id }}</p>
          <p>
            <strong>Status:</strong>
            <span :class="slot.status == 'O' ? 'text-danger' : 'text-success'">
              {{ slot.status == 'O' ? 'Occupied' : 'Available' }}
            </span>
          </p>
          <p><strong>Lot ID:</strong> {{ lot.name }}</p>
          <p><strong>Label:</strong> {{ slot.label }}</p>
          <p><strong>User:</strong> {{ slot.user_name }}</p>
          <p><strong>Driver Name:</strong> {{ slot.driver_name }}</p>
          <p><strong>Driver Contact:</strong> {{ slot.driver_contact }}</p>
          <p><strong>Vehicle Number:</strong> {{ slot.vehicle_number }}</p>
          <p><strong>Start Time:</strong> {{ f_date(slot.occupied_since) }}</p>
          <p><strong>End Time:</strong> {{ f_date(slot.end_time) }}</p>
          <p v-if="slot.total_earnings"><strong>Total Earnings:</strong> ${{ slot.total_earnings }}</p>
        </div>

        <div class="modal-footer">
          <button type="submit" class="btn btn-success" v-if="slot.status == 'A'"
            @click="$emit('deleteSlot', slot)">Delete</button>
          <button type="button" class="btn btn-secondary" @click="$emit('close')">Close</button>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'
const f_date = (raw) => raw ? new Date(raw).toLocaleString() : '';
const props = defineProps({
  visible: { type: Boolean, default: false },
  slot: { type: Object, default: () => ({}) },
  lot: { type: Object, default: () => ({}) }
})
</script>
