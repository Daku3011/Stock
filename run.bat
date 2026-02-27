@echo off
REM Stock Dashboard - Windows Run Script

echo ================================
echo 🤖 Stock Analysis Dashboard
echo ================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt -q

REM Run the app
echo.
echo 🚀 Starting application...
echo 📍 Open http://127.0.0.1:5000 in your browser
echo.

python app.py

pause
