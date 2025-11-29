import { createApp } from "vue"
import { createPinia } from "pinia";
import App from "./App.vue"
import router from "./router"
import Toast from "vue-toastification";
import "vue-toastification/dist/index.css";

import { Chart as ChartJS, registerables } from 'chart.js';
import "bootstrap/dist/css/bootstrap.min.css"
import "bootstrap/dist/js/bootstrap.bundle.min.js"


const app = createApp(App);

app.config.devtools = true 

app.use(createPinia());  
app.use(router);
app.use(Toast);

app.mount("#app");

ChartJS.register(...registerables);
// createApp(App).use(router).mount("#app")


