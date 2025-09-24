# start_project.ps1 - fully configure project local env and run Flask + Vue

$ProjectDir = Get-Location
$VenvDir = Join-Path $ProjectDir "venv"

Write-Host "Starting project setup in $ProjectDir"

# 1️⃣ Create venv if missing
if (-Not (Test-Path $VenvDir)) {
    Write-Host "Creating Python virtual environment..."
    python -m venv venv
}

# 2️⃣ Activate venv
Write-Host "Activating virtual environment..."
& "$VenvDir\Scripts\Activate.ps1"

# 3️⃣ Upgrade pip
Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

# 4️⃣ Install Python dependencies
if (Test-Path "requirements.txt") {
    Write-Host "Installing Python dependencies..."
    python -m pip install -r requirements.txt
}

# 5️⃣ Test critical packages
python -c "import flask_cors; import flask_caching; import flask_sqlalchemy; Write-Host('Python imports OK')"

# 6️⃣ Set Flask environment variables
if (-Not $env:FLASK_APP) { $env:FLASK_APP = "backend/app.py" }
$env:FLASK_ENV = "development"

# 7️⃣ Start Flask server in background
Write-Host "Starting Flask server..."
Start-Process "flask" "run"

# 8️⃣ Start Vue dev server if frontend exists
$FrontendDir = Join-Path $ProjectDir "frontend"
if (Test-Path $FrontendDir) {
    Write-Host "Starting Vue dev server..."
    Set-Location $FrontendDir
    if (Test-Path "package.json") {
        npm install
        Start-Process "npm" "run serve"
    }
    Set-Location $ProjectDir
}

Write-Host "Project setup complete. Flask + Vue running."

