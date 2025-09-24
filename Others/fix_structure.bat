@echo off
set ROOT_DIR=%cd%
set FRONTEND_DIR=%ROOT_DIR%\frontend
set BACKEND_DIR=%ROOT_DIR%\backend

echo Restructuring project under %ROOT_DIR%...

REM --- Frontend cleanup ---
echo Fixing frontend...
if not exist "%FRONTEND_DIR%\src\components" mkdir "%FRONTEND_DIR%\src\components"
if not exist "%FRONTEND_DIR%\src\views" mkdir "%FRONTEND_DIR%\src\views"

REM Move vue-project into frontend
if exist "%ROOT_DIR%\vue-project\" (
  xcopy "%ROOT_DIR%\vue-project\*" "%FRONTEND_DIR%\" /E /H /Y
  rmdir /S /Q "%ROOT_DIR%\vue-project"
)

REM Move src\app.js -> frontend\src\main.js
if exist "%ROOT_DIR%\src\app.js" (
  move "%ROOT_DIR%\src\app.js" "%FRONTEND_DIR%\src\main.js"
  rmdir /S /Q "%ROOT_DIR%\src"
)

REM Rename .js to .vue in components
for %%f in ("%FRONTEND_DIR%\src\components\*.js") do (
  ren "%%f" "%%~nf.vue"
)

REM --- Backend cleanup ---
echo Fixing backend...
if not exist "%BACKEND_DIR%\instance" mkdir "%BACKEND_DIR%\instance"

REM --- Gitignore ---
echo Creating .gitignore...
(
echo # Global ignores
echo *.pyc
echo __pycache__/
echo *.ini
echo *.log
echo *.sqlite3
echo *.db
echo .DS_Store
echo .env
echo venv/
echo node_modules/
) > "%ROOT_DIR%\.gitignore"

echo Project restructure complete.
