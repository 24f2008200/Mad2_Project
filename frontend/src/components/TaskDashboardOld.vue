<template>
  <div class="container mt-4">

    <div class="d-flex justify-content-between align-items-center mb-3">
      <h3>Celery Task Dashboard</h3>

      <div>
        <button class="btn btn-success me-2" @click="openRunModal">
          Run Task
        </button>

        <button class="btn btn-primary" @click="loadTasks">
          Refresh
        </button>
      </div>
    </div>

    <input class="form-control mb-3" v-model="search" placeholder="Search tasks…" />

    <table class="table table-bordered table-hover">
      <thead class="table-light">
        <tr>
          <th>ID</th>
          <th>Status</th>
          <th>Result</th>
          <th>Time</th>
          <th>Actions</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="task in filteredTasks" :key="task.id">
          <td style="max-width:150px; word-break: break-all">{{ task.id }}</td>

          <td>
            <span :class="statusClass(task.status)">{{ task.status }}</span>
          </td>

          <td>{{ summary(task.result) }}</td>
          <td>{{ task.date_done || "—" }}</td>

          <td>
            <button class="btn btn-sm btn-outline-secondary me-1"
                    @click="openModal(task)">
              View
            </button>

            <button v-if="isCancelable(task.status)"
                    class="btn btn-sm btn-danger"
                    @click="cancel(task.id)">
              Cancel
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Task Details Modal -->
    <div class="modal fade" ref="modal" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">

          <div class="modal-header">
            <h5 class="modal-title">Task Details</h5>
            <button class="btn-close" @click="closeModal"></button>
          </div>

          <div class="modal-body">
            <pre>{{ selectedTask }}</pre>
          </div>

        </div>
      </div>
    </div>

    <!-- RUN TASK MODAL -->
    <div class="modal fade" ref="runModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">

          <div class="modal-header">
            <h5 class="modal-title">Run a Task</h5>
            <button class="btn-close" @click="closeRunModal"></button>
          </div>

          <div class="modal-body">

            <div class="mb-3">
              <label class="form-label">Task Name (Dot path)</label>
              <input class="form-control" v-model="taskName"
                     placeholder="backend.tasks.rules.run_rule" />
            </div>

            <div class="mb-3">
              <label class="form-label">Args (JSON array)</label>
              <input class="form-control" v-model="taskArgs" placeholder='[1, 2, 3]' />
            </div>

            <div class="mb-3">
              <label class="form-label">Kwargs (JSON dict)</label>
              <input class="form-control" v-model="taskKwargs" placeholder='{"x":1}' />
            </div>

          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="closeRunModal">Close</button>
            <button class="btn btn-success" @click="runTaskNow">
              Run
            </button>
          </div>

        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import taskService from "../services/taskService";

const tasks = ref([]);
const search = ref("");
const selectedTask = ref(null);

const modal = ref(null);
const runModal = ref(null);

const taskName = ref("");
const taskArgs = ref("[]");
const taskKwargs = ref("{}");


async function loadTasks() {
  tasks.value = await taskService.getAll();
}

// Cancel
async function cancel(id) {
  await taskService.cancelTask(id);
  loadTasks();
}

function isCancelable(status) {
  return ["PENDING", "RECEIVED", "STARTED", "RETRY"].includes(status);
}

// Run Task manually
async function runTaskNow() {
  try {
    const args = JSON.parse(taskArgs.value || "[]");
    const kwargs = JSON.parse(taskKwargs.value || "{}");

    const res = await taskService.runTask(taskName.value, args, kwargs);
    alert("Task started: " + res.task_id);

    closeRunModal();
    loadTasks();
  } catch (e) {
    alert("Invalid JSON");
  }
}

// Helpers
const filteredTasks = computed(() =>
  tasks.value.filter(
    t =>
      t.id.toLowerCase().includes(search.value.toLowerCase()) ||
      t.status.toLowerCase().includes(search.value.toLowerCase())
  )
);

function summary(result) {
  if (!result) return "—";
  let s = JSON.stringify(result);
  return s.length > 30 ? s.substring(0, 30) + "..." : s;
}

function statusClass(status) {
  if (status === "SUCCESS") return "badge bg-success";
  if (status === "FAILURE") return "badge bg-danger";
  if (status === "PENDING") return "badge bg-warning text-dark";
  return "badge bg-secondary";
}

// Modals
function openModal(task) {
  selectedTask.value = JSON.stringify(task, null, 2);
  $(modal.value).modal("show");
}

function closeModal() {
  $(modal.value).modal("hide");
}

function openRunModal() {
  $(runModal.value).modal("show");
}

function closeRunModal() {
  $(runModal.value).modal("hide");
}

onMounted(() => {
  loadTasks();
  // setInterval(loadTasks, 3000);
});
</script>
