#!/bin/bash
# start_flask.sh - setup venv, install deps, run Flask

PROJECT_DIR=$(pwd)
VENV_DIR="$PROJECT_DIR/venv"

# 1️⃣ Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# 2️⃣ Activate venv
source "$VENV_DIR/Scripts/activate"

# 3️⃣ Upgrade pip
python -m pip install --upgrade pip

# 4️⃣ Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    python -m pip install -r requirements.txt
fi

# 5️⃣ Test key packages
python -c "import flask_cors; import flask_caching; import flask_sqlalchemy; print('Imports OK')"

# 6️⃣ Set FLASK_APP if not already
export FLASK_APP=${FLASK_APP:-app.py}
export FLASK_ENV=development

# 7️⃣ Run Flask
echo "Starting Flask server..."
flask run
