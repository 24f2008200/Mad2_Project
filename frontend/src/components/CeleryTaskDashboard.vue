<template>
    <div class="container mt-4">

        <!-- Search -->
        <input v-model="searchText" class="form-control mb-3" placeholder="Search tasks..." />

        <!-- Buttons -->
        <div class="d-flex mb-3">
            <button class="btn btn-success me-2" @click="runTask">Run Task</button>
            <button class="btn btn-primary" @click="loadTasks">Refresh</button>
        </div>

        <!-- Table -->
        <table class="table table-striped table-bordered">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Progress</th>
                    <th>Duration</th>
                    <th>Start Time</th>
                    <th>End Time</th>
                </tr>
            </thead>

            <tbody>
                <tr v-for="task in filteredTasks" :key="task.id">
                    <td>{{ task.id }}</td>
                    <td>{{ task.name }}</td>
                    <td>
                        <span :class="statusClass(task.status)">
                            {{ task.status }}
                        </span>
                    </td>
                    <td>{{ task.progress }}%</td>
                    <td>{{ task.duration?.toFixed(2) }}s</td>
                    <td>{{ formatDate(task.start_time) }}</td>
                    <td>{{ formatDate(task.end_time) }}</td>
                </tr>
            </tbody>
        </table>

    </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import apiClient from '@/apiClient';

const tasks = ref([]);
const searchText = ref("");

// Fetch tasks
const loadTasks = async () => {
    try {
        const res = await apiClient.get("/tasks");
        const payload = res?.data ?? res;

        tasks.value = payload.tasks ?? [];
        console.log("Loaded tasks:", tasks.value);
    } catch (err) {
        console.error("Error loading tasks", err);
    }
};

// Run a demo task
const runTask = async () => {
    try {
        await apiClient.post("/run-task");
        loadTasks();
    } catch (e) {
        console.error("Failed to run task", e);
    }
};

// Search filter
const filteredTasks = computed(() => {

    if (!searchText.value) return tasks.value;

    return tasks.value.filter((t) => {
        console.log("Searching task:", t);
        return JSON.stringify(t).toLowerCase().includes(searchText.value.toLowerCase());
    });
});

// Utility – status color
const statusClass = (status) => {
    return {
        "text-success": status === "SUCCESS",
        "text-danger": status === "FAILED",
        "text-warning": status === "RUNNING",
    };
};

// Utility – format date
const formatDate = (dt) => {
    if (!dt) return "-";
    return new Date(dt).toLocaleString();
};

// Load on page mount
onMounted(() => loadTasks());
</script>

<style scoped>
.text-success {
    font-weight: bold;
}

.text-danger {
    font-weight: bold;
}

.text-warning {
    font-weight: bold;
}
</style>
