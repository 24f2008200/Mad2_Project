# Go to project root
Set-Location $PSScriptRoot

# Create venv if missing
if (-Not (Test-Path "venv")) {
    python -m venv venv
}

# Activate venv
. .\venv\Scripts\Activate.ps1

# Install requirements if available
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
}

Write-Host "✅ Project ready in local venv"
