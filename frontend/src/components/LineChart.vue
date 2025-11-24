<template>
  <div class="card">
    <canvas ref="canvas"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
} from "chart.js";

// register components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend
);

const props = defineProps({
  data: {
    type: Array,
    required: true,
  },
});

const canvas = ref(null);
let chartInstance = null;

function renderChart() {
  const months = props.data.map((d) => d.month);
  const amounts = props.data.map((d) => d.amount);

  if (chartInstance) {
    chartInstance.destroy();
  }

  chartInstance = new Chart(canvas.value, {
    type: "line",
    data: {
      labels: months,
      datasets: [
        {
          label: "Revenue",
          data: amounts,
          borderColor: "#007bff",
          backgroundColor: "rgba(0, 123, 255, 0.2)",
          borderWidth: 2,
          tension: 0.3,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: { title: { display: true, text: "Month" } },
        y: { title: { display: true, text: "Revenue" } },
      },
    },
  });
}

onMounted(() => {
  renderChart();
});

watch(
  () => props.data,
  () => renderChart(),
  { deep: true }
);
</script>
