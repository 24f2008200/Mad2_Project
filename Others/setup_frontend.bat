@echo off
setlocal

set ROOT_DIR=%cd%
set FRONTEND_DIR=%ROOT_DIR%\frontend
set SRC_DIR=%FRONTEND_DIR%\src
set COMPONENTS_DIR=%SRC_DIR%\components
set VIEWS_DIR=%SRC_DIR%\views

echo Setting up Vue frontend structure in %FRONTEND_DIR%...

REM --- Create folders ---
if not exist "%SRC_DIR%" mkdir "%SRC_DIR%"
if not exist "%COMPONENTS_DIR%" mkdir "%COMPONENTS_DIR%"
if not exist "%VIEWS_DIR%" mkdir "%VIEWS_DIR%"

REM --- main.js ---
(
echo import ^{ createApp ^} from "vue";
echo import App from "./App.vue";
echo import router from "./router";
echo.
echo import "bootstrap/dist/css/bootstrap.min.css";
echo import "bootstrap";
echo.
echo createApp(App^)^
echo   .use(router^)^
echo   .mount("#app");
) > "%SRC_DIR%\main.js"

REM --- App.vue ---
(
echo ^<template^>
echo   ^<div^>
echo     ^<Navbar /^>
echo     ^<div class="container mt-4"^>
echo       ^<router-view /^>
echo     ^</div^>
echo   ^</div^>
echo ^</template^>
echo.
echo ^<script^>
echo import Navbar from "./components/Navbar.vue";
echo export default ^{ name: "App", components: ^{ Navbar ^} ^};
echo ^</script^>
echo.
echo ^<style^>
echo body ^{ background-color: #f8f9fa; ^}
echo ^</style^>
) > "%SRC_DIR%\App.vue"

REM --- router.js ---
(
echo import ^{ createRouter, createWebHistory ^} from "vue-router";
echo import Home from "./views/Home.vue";
echo import Admin from "./views/Admin.vue";
echo.
echo const routes = [
echo   ^{ path: "/", component: Home ^},
echo   ^{ path: "/admin", component: Admin ^}
echo ];
echo.
echo const router = createRouter(^{
echo   history: createWebHistory(^),
echo   routes
echo ^});
echo.
echo export default router;
) > "%SRC_DIR%\router.js"

REM --- Home.vue ---
(
echo ^<template^>
echo   ^<div^>
echo     ^<h1^>Welcome to Vehicle Parking^</h1^>
echo     ^<LotsDashboard /^>
echo   ^</div^>
echo ^</template^>
echo.
echo ^<script^>
echo import LotsDashboard from "../components/LotsDashboard.vue";
echo export default ^{ name: "Home", components: ^{ LotsDashboard ^} ^};
echo ^</script^>
) > "%VIEWS_DIR%\Home.vue"

REM --- Admin.vue ---
(
echo ^<template^>
echo   ^<div^>
echo     ^<AdminDashboard /^>
echo   ^</div^>
echo ^</template^>
echo.
echo ^<script^>
echo import AdminDashboard from "../components/AdminDashboard.vue";
echo export default ^{ name: "Admin", components: ^{ AdminDashboard ^} ^};
echo ^</script^>
) > "%VIEWS_DIR%\Admin.vue"

REM --- Navbar.vue ---
(
echo ^<template^>
echo   ^<nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3"^>
echo     ^<a class="navbar-brand" href="#"^>Vehicle Parking^</a^>
echo     ^<div class="navbar-nav ms-auto"^>
echo       ^<RouterLink class="nav-link" to="/"^>Home^</RouterLink^>
echo       ^<RouterLink class="nav-link" to="/admin"^>Admin^</RouterLink^>
echo     ^</div^>
echo   ^</nav^>
echo ^</template^>
echo.
echo ^<script^>
echo export default ^{ name: "Navbar" ^};
echo ^</script^>
echo.
echo ^<style scoped^>
echo .navbar-brand ^{ font-weight: bold; ^}
echo ^</style^>
) > "%COMPONENTS_DIR%\Navbar.vue"

REM --- AdminDashboard.vue ---
(
echo ^<template^>
echo   ^<div class="container mt-4"^>
echo     ^<h2^>Admin Dashboard^</h2^>
echo     ^<p class="text-muted"^>Manage parking lots and spots here.^</p^>
echo   ^</div^>
echo ^</template^>
echo.
echo ^<script^>
echo export default ^{ name: "AdminDashboard" ^};
echo ^</script^>
) > "%COMPONENTS_DIR%\AdminDashboard.vue"

REM --- ParkingLotCard.vue ---
(
echo ^<template^>
echo   ^<div class="card"^>
echo     ^<div class="card-body"^>
echo       ^<h5^>{{ lot.name }}^</h5^>
echo       ^<p^>Address: {{ lot.address }}^</p^>
echo     ^</div^>
echo   ^</div^>
echo ^</template^>
echo.
echo ^<script^>
echo export default ^{ name: "ParkingLotCard", props: ^{ lot: Object ^} ^};
echo ^</script^>
) > "%COMPONENTS_DIR%\ParkingLotCard.vue"

REM --- LotsDashboard.vue ---
(
echo ^<template^>
echo   ^<div class="container mt-4"^>
echo     ^<h2^>Available Parking Lots^</h2^>
echo   ^</div^>
echo ^</template^>
echo.
echo ^<script^>
echo export default ^{ name: "LotsDashboard" ^};
echo ^</script^>
) > "%COMPONENTS_DIR%\LotsDashboard.vue"

echo ✅ Frontend Vue files created successfully!
endlocal
