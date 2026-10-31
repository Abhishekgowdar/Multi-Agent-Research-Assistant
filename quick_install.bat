@echo off
REM Quick installation - installs only essential packages

echo 🚀 Quick Install - Essential Packages Only
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo Installing essential packages...
pip install --quiet google-generativeai chromadb arxiv requests loguru click rich pyyaml python-dotenv pydantic tenacity
echo.

echo ✅ Quick install complete!
echo.
echo Testing setup...
python test_setup.py
echo.

pause
