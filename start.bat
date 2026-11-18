@echo off
setlocal
set "VENV_DIR="

for %%d in (venv .venv env avenv) do (
    if exist "%%d\Scripts\activate.bat" (
        set "VENV_DIR=%%d"
        goto :found_venv
    )
)

:: If no venv exists, create .venv
set "VENV_DIR=.venv"
echo No valid virtual environment found. Creating one in '%VENV_DIR%'...
python -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo Error: Python is not installed or not found in PATH.
    pause
    exit /b 1
)
echo Virtual environment created successfully.

:found_venv
set "PYTHON_BIN=%VENV_DIR%\Scripts\python.exe"

if exist "requirements.txt" (
    set "MARKER_FILE=%VENV_DIR%\.requirements_installed"
    if not exist "%MARKER_FILE%" (
        echo Installing/updating requirements from requirements.txt...
        "%PYTHON_BIN%" -m pip install --upgrade pip
        "%PYTHON_BIN%" -m pip install -r requirements.txt
        type nul > "%MARKER_FILE%"
    ) else (
        echo Dependencies are up to date. Skipping pip install.
    )
)

if exist "main.py" (
    echo Running main.py...
    "%PYTHON_BIN%" main.py
) else (
    echo Error: main.py not found in the current directory!
    pause
)
endlocal
