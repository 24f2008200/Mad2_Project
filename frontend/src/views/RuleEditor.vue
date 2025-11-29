<template>
  <div class="card p-3">
    <h3>{{ isEdit ? 'Edit Rule' : 'New Rule' }}</h3>

    <div class="mb-2">
      <label class="form-label">Name</label>
      <input v-model="form.name" class="form-control" />
    </div>

    <div class="mb-2">
      <label class="form-label">Description</label>
      <textarea v-model="form.description" class="form-control"></textarea>
    </div>

    <!-- Schedule: type selector -->
    <div class="mb-2 row">
      <div class="col-4">
        <label class="form-label">Schedule Type</label>
        <select v-model="form.schedule.type" class="form-select">
          <option value="daily">Daily</option>
          <option value="monthly">Monthly</option>
          <option value="cron">Cron</option>
        </select>
      </div>

      <div class="col-4" v-if="form.schedule.type === 'daily'">
        <label class="form-label">Daily Time (HH:MM) or Time Field</label>
        <input v-model="form.schedule.time" placeholder="18:00" class="form-control" />
        <small class="form-text text-muted">If you prefer per-user use time_field e.g. "reminder_time" in target</small>
      </div>

      <div class="col-4" v-if="form.schedule.type === 'monthly'">
        <label class="form-label">Day & Time</label>
        <div class="d-flex">
          <input v-model.number="form.schedule.day" type="number" class="form-control me-2" min="1" max="28" />
          <input v-model="form.schedule.time" placeholder="02:00" class="form-control" />
        </div>
      </div>

      <div class="col-8 mt-2" v-if="form.schedule.type === 'cron'">
        <label class="form-label">Cron Expression</label>
        <input v-model="form.schedule.expr" class="form-control" placeholder="0 18 * * *" />
      </div>
    </div>

    <!-- Conditions -->
    <div class="mb-2">
      <label class="form-label">Conditions</label>
      <div v-for="(c, idx) in form.conditions" :key="idx" class="card p-2 mb-2">
        <div class="d-flex gap-2 align-items-center">
          <select v-model="c.name" class="form-select w-50">
            <option value="not_visited_in_days">Not visited in days</option>
            <option value="has_booked_in_days">Has booked in days</option>
            <option value="spent_more_than">Spent more than</option>
            <option value="most_used_parkinglot_in_period">Most-used parkinglot in period</option>
            <option value="has_parkinglot_created_by_admin_in_days">Lot created by admin in last X</option>
          </select>
          <input v-model="c.days" v-if="needsDays(c.name)" type="number" class="form-control w-25" placeholder="days" />
          <input v-model="c.amount" v-if="c.name === 'spent_more_than'" type="number" class="form-control w-25" placeholder="amount" />
          <input v-model="c.min_count" v-if="c.name === 'most_used_parkinglot_in_period'" type="number" class="form-control w-25" placeholder="min_count" />
          <button class="btn btn-danger btn-sm" @click="removeCondition(idx)">Remove</button>
        </div>
      </div>
      <button class="btn btn-secondary btn-sm" @click="addCondition">Add condition</button>
    </div>

    <!-- Actions -->
    <div class="mb-2">
      <label class="form-label">Actions</label>
      <div v-for="(a, idx) in form.actions" :key="idx" class="d-flex gap-2 align-items-center mb-2">
        <select v-model="a.action" class="form-select w-50">
          <option value="send_reminder">Send reminder</option>
          <option value="generate_and_email_report">Generate monthly report</option>
        </select>
        <input v-model="a.channels" placeholder='channels e.g. ["gchat","email"]' class="form-control" />
        <button class="btn btn-danger btn-sm" @click="removeAction(idx)">Remove</button>
      </div>
      <button class="btn btn-secondary btn-sm" @click="addAction">Add action</button>
    </div>

    <div class="d-flex gap-2 mt-3">
      <button class="btn btn-primary" @click="save">Save</button>
      <button class="btn btn-outline-primary" @click="preview">Preview</button>
      <button class="btn btn-outline-secondary" @click="resetForm">Reset</button>
    </div>

    <div v-if="previewResult" class="mt-3">
      <h5>Preview (matched_count: {{ previewResult.matched_count }})</h5>
      <table class="table table-sm">
        <thead><tr><th>id</th><th>name</th><th>email</th><th>last_login_ist</th><th>reminder_time</th></tr></thead>
        <tbody>
          <tr v-for="u in previewResult.sample" :key="u.id">
            <td>{{ u.id }}</td><td>{{ u.name }}</td><td>{{ u.email }}</td><td>{{ u.last_login_ist }}</td><td>{{ u.reminder_time }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import apiClient from "@/apiClient"
import { ref, reactive, computed } from "vue";

export default {
  props: {
    ruleId: { type: Number, default: null } // pass to edit
  },
  setup(props) {
    const isEdit = ref(!!props.ruleId);
    const form = reactive({
      name: "",
      description: "",
      enabled: true,
      schedule: { type: "daily", time: "18:00" },
      conditions: [],
      actions: [],
      target: null
    });
    const previewResult = ref(null);

    function needsDays(name) {
      return ["not_visited_in_days", "has_booked_in_days", "most_used_parkinglot_in_period", "has_parkinglot_created_by_admin_in_days"].includes(name);
    }

    function addCondition() {
      form.conditions.push({ name: "not_visited_in_days", days: 7 });
    }
    function removeCondition(i) { form.conditions.splice(i, 1); }

    function addAction() {
      form.actions.push({ action: "send_reminder", channels: ['gchat'] });
    }
    function removeAction(i) { form.actions.splice(i, 1); }

    async function save() {
      try {
        if (isEdit.value) {
          await apiClient.put(`/admin/rules/${props.ruleId}`, form);
        } else {
          await apiClient.post(`/admin/rules`, form);
        }
        alert("Saved");
      } catch (e) {
        alert("Save failed: " + (e.response?.data?.error || e.message));
      }
    }

    async function preview() {
      try {
        const resp = await apiClient.post(`/admin/preview_rule/${props.ruleId || 0}`, { limit: 10 });
        previewResult.value = resp.data;
      } catch (e) {
        // if creating new (no id) send payload to preview endpoint that accepts a rule object?
        // Fallback: call preview with inline rule creation (optional) - here we ask server to support preview via POST with rule body in future.
        alert("Preview failed: " + (e.response?.data?.error || e.message));
      }
    }

    function resetForm() {
      form.name = "";
      form.description = "";
      form.schedule = { type: "daily", time: "18:00" };
      form.conditions = [];
      form.actions = [];
      previewResult.value = null;
    }

    return {
      isEdit, form, addCondition, removeCondition, addAction, removeAction, save, preview, previewResult, needsDays, resetForm
    };
  }
};
</script>

<style scoped>
.card { max-width: 900px; margin: 12px auto; }
</style>
