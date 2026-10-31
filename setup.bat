@echo off
REM Setup script for Multi-Agent Research Assistant (Windows)

echo 🤖 Setting up Multi-Agent Research Assistant...
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Copy .env.example to .env
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo.
    echo ⚠️  IMPORTANT: Edit .env and add your GEMINI_API_KEY
    echo    Get it free from: https://makersuite.google.com/app/apikey
    echo.
) else (
    echo .env file already exists
    echo.
)

REM Create data directory
echo Creating data directory...
mkdir data 2>nul
echo.

echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Edit .env and add your GEMINI_API_KEY
echo 2. Run: python -m src.main "your research query"
echo.

pause
