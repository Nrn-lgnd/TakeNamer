#!/bin/bash

VENV_DIR=""
for dir in venv .venv env avenv; do
    if [ -d "$dir" ]; then
        # Check if it has an activation script to ensure it's a valid venv
        if [ -f "$dir/bin/activate" ] || [ -f "$dir/Scripts/activate" ]; then
            VENV_DIR="$dir"
            break
        fi
    fi
done

# If no valid virtual environment was found, create a new one (.venv)
if [ -z "$VENV_DIR" ]; then
    VENV_DIR=".venv"
    echo "No valid virtual environment found. Creating one in '$VENV_DIR'..."

    if command -v python3 &> /dev/null; then
        python3 -m venv "$VENV_DIR"
    elif command -v python &> /dev/null; then
        python -m venv "$VENV_DIR"
    else
        echo "Error: Python is not installed or not found in PATH."
        exit 1
    fi
    echo "Virtual environment created successfully."
else
    echo "Venv directory found: $VENV_DIR"
fi

# Determine the correct Python binary path inside the venv
if [ -f "$VENV_DIR/bin/python3" ]; then
    PYTHON_BIN="$VENV_DIR/bin/python3"
elif [ -f "$VENV_DIR/bin/python" ]; then
    PYTHON_BIN="$VENV_DIR/bin/python"
elif [ -f "$VENV_DIR/Scripts/python.exe" ]; then
    PYTHON_BIN="$VENV_DIR/Scripts/python.exe"
elif [ -f "$VENV_DIR/Scripts/python" ]; then
    PYTHON_BIN="$VENV_DIR/Scripts/python"
else
    echo "Error: Could not locate Python binary inside '$VENV_DIR'."
    exit 1
fi

# Install requirements only if needed (first time or if requirements.txt changed)
if [ -f "requirements.txt" ]; then
    MARKER_FILE="$VENV_DIR/.requirements_installed"

    # Check if marker doesn't exist OR if requirements.txt is newer than the marker
    if [ ! -f "$MARKER_FILE" ] || [ "requirements.txt" -nt "$MARKER_FILE" ]; then
        echo "Installing/updating requirements from requirements.txt..."
        "$PYTHON_BIN" -m pip install --upgrade pip
        "$PYTHON_BIN" -m pip install -r requirements.txt

        # Update/create the marker file timestamp
        touch "$MARKER_FILE"
    else
        echo "Dependencies are up to date. Skipping pip install."
    fi
else
    echo "Notice: requirements.txt not found, skipping dependency installation."
fi

# Run main.py using the virtual environment's python binary
if [ -f "main.py" ]; then
    echo "Running main.py..."
    "$PYTHON_BIN" main.py
else
    echo "Error: main.py not found in the current directory!"
    exit 1
fi
