@echo off
echo PDF Processing Automation
echo ========================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if config.py exists
if not exist config.py (
    echo Error: config.py not found. Please run setup.py first.
    pause
    exit /b 1
)

echo Starting PDF processing...
python pdf_processor.py

echo.
echo Processing complete. Check pdf_processor.log for details.
pause
