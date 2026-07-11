@echo off
title CTResumeBuilder

cd /d "%~dp0"

echo ================================
echo CTResumeBuilder
echo ================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo.
echo Installing/updating requirements...
pip install -r requirements.txt

echo.
echo Starting application...
start http://127.0.0.1:5050
python app.py

pause
