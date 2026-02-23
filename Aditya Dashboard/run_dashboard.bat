@echo off
REM ============================================================================
REM Weelocal Dashboard - Professional Startup Script
REM ============================================================================
REM This script starts the Weelocal Dashboard server
REM
REM Requirements:
REM   - Python 3.14+ installed
REM   - Flask installed (pip install flask)
REM   - Run from dashboard directory
REM
REM Usage:
REM   run_dashboard.bat
REM
REM Access:
REM   http://localhost:8000
REM ============================================================================

setlocal enabledelayedexpansion

cls
echo ============================================================================
echo WEELOCAL DASHBOARD STARTUP
echo ============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.14+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if Flask is installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Flask is not installed
    echo Installing Flask...
    pip install -q flask
    if errorlevel 1 (
        echo ERROR: Could not install Flask
        echo Run: pip install flask
        pause
        exit /b 1
    )
)

REM Check if required files exist
if not exist "run_server.py" (
    echo ERROR: run_server.py not found
    echo Please run this script from the dashboard directory
    pause
    exit /b 1
)

if not exist "dashboard.html" (
    echo ERROR: dashboard.html not found
    echo Please ensure all files are in this directory
    pause
    exit /b 1
)

if not exist "data.json" (
    echo ERROR: data.json not found
    echo Please ensure all files are in this directory
    pause
    exit /b 1
)

echo Checking dependencies...
echo  DONE
echo.

REM Start the server
echo ============================================================================
echo Starting Weelocal Dashboard Server
echo ============================================================================
echo.
echo Server will start on: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.
echo ============================================================================
echo.

python run_server.py

echo.
echo ============================================================================
echo Server stopped
echo ============================================================================
pause
)

echo.
echo [2/3] Starting local server...
echo.
echo Dashboard will open at: http://localhost:8000/dashboard.html
echo Press Ctrl+C to stop the server
echo.

python serve_dashboard.py

pause
