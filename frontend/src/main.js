import { createApp } from "vue"
import { createPinia } from "pinia";
import App from "./App.vue"
import router from "./router"


import "bootstrap/dist/css/bootstrap.min.css"
import "bootstrap/dist/js/bootstrap.bundle.min.js"


const app = createApp(App);

app.config.devtools = true 

app.use(createPinia());  
app.use(router);

app.mount("#app");


// createApp(App).use(router).mount("#app")
