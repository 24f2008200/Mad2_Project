<template>
  <div>
    <Navbar />
    <!-- <div class="container mt-4"> -->
      <div class="container-fluid mt-4">
      <router-view />
    </div>
  </div>
</template>

<script>
import Navbar from "./components/Navbar.vue";
export default { name: "App", components: { Navbar } };
</script>

<style>
body { background-color: #f8f9fa; }
</style>
