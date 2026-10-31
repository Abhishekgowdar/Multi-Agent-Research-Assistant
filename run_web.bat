@echo off
echo 🚀 Starting AI Research Assistant Web UI...
echo.
echo 📍 Open your browser to: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d %~dp0
call venv\Scripts\activate.bat
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
