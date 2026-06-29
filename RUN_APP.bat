@echo off
cd /d "%~dp0"
echo Closing old CTResumeBuilder servers on port 5000/5050 if any...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000"') do taskkill /F /PID %%a >nul 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5050"') do taskkill /F /PID %%a >nul 2>nul
python -m pip install -r requirements.txt
python run_app.py
pause
