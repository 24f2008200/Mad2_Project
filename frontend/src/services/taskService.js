import apiClient from "@/apiClient"

export default {

  async getAll() {
    const res = await apiClient.get("/tasks");
    return res.data;
  },

  async cancelTask(taskId) {
    const res = await apiClient.get(`/tasks/${taskId}/cancel`);
    return res.data;
  },

  async runTask(taskName, args = [], kwargs = {}) {
    const res = await apiClient.get("/tasks/run", {
      task: taskName,
      args,
      kwargs,
    });
    return res.data;
  },

};
