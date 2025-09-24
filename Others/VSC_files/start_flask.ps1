# start_flask.ps1 - setup venv, install deps, run Flask

$ProjectDir = Get-Location
$VenvDir = Join-Path $ProjectDir "venv"

# 1️⃣ Create venv if missing
if (-Not (Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

# 2️⃣ Activate venv
& "$VenvDir\Scripts\Activate.ps1"

# 3️⃣ Upgrade pip
python -m pip install --upgrade pip

# 4️⃣ Install requirements
if (Test-Path "requirements.txt") {
    Write-Host "Installing requirements..."
    python -m pip install -r requirements.txt
}

# 5️⃣ Test key packages
python -c "import flask_cors; import flask_caching; import flask_sqlalchemy; Write-Host('Imports OK')"

# 6️⃣ Set environment variables
if (-Not $env:FLASK_APP) { $env:FLASK_APP = "app.py" }
$env:FLASK_ENV = "development"

# 7️⃣ Run Flask
Write-Host "Starting Flask server..."
flask run
