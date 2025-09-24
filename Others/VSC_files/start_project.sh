#!/bin/bash
# start_project.sh - fully configure project local env and run Flask + Vue

PROJECT_DIR=$(pwd)
VENV_DIR="$PROJECT_DIR/venv"

echo "Starting project setup in $PROJECT_DIR"

# 1️⃣ Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# 2️⃣ Activate venv
echo "Activating virtual environment..."
source "$VENV_DIR/Scripts/activate"

# 3️⃣ Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# 4️⃣ Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    python -m pip install -r requirements.txt
fi

# 5️⃣ Test critical packages
python -c "import flask_cors; import flask_caching; import flask_sqlalchemy; print('Python imports OK')"

# 6️⃣ Set Flask env vars
export FLASK_APP=${FLASK_APP:-backend/app.py}
export FLASK_ENV=development

# 7️⃣ Start Flask server in background
echo "Starting Flask server..."
flask run &

# 8️⃣ Start Vue dev server if frontend exists
if [ -d "frontend" ]; then
    echo "Starting Vue dev server..."
    cd frontend
    if [ -f "package.json" ]; then
        npm install
        npm run serve
    fi
    cd ..
fi

echo "Project setup complete. Flask + Vue running."
