@echo off
title MOJ E-Notary Automation - Setup
echo.
echo ============================================
echo   MOJ E-Notary WhatsApp Automation System
echo   Setup Script
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

echo [OK] Virtual environment created
echo.

REM Activate and install
echo Installing dependencies...
call venv\Scriptsctivate
pip install -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Some dependencies may have failed
    echo Please check the output above
)

echo [OK] Dependencies installed
echo.

REM Create directories
echo Creating directories...
mkdir data 2>nul
mkdir logs 2>nul
mkdir backups 2>nul
mkdir chrome_profile 2>nul
echo [OK] Directories created
echo.

REM Run setup script
echo Running configuration setup...
python setup.py

echo.
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo To start the system:
echo   1. Edit config\groups.json with your group names
echo   2. Run: python main.py
echo.
echo For headless mode (after first login):
echo   python main.py --headless --no-ui
echo.
pause
