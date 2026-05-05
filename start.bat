@echo off
title BiomassML - Energy Simulation Server
echo.
echo  ============================================
echo   BiomassML - Biomass Grinding Energy Simulation
echo   ECE Major Project - Suhani Tyagi ^& Vaishali Kasotiya
echo  ============================================
echo.

:: Check Python
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: Install dependencies if needed
echo [*] Checking dependencies...
pip install -r requirements.txt -q

echo.
echo [*] Starting server at http://localhost:8080
echo [*] Press Ctrl+C to stop
echo.
start "" "http://localhost:8080"
python app.py
pause
