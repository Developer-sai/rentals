@echo off
echo.
echo ^|  IrishHome.AI — Starting up (Windows)
echo ^|━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo X  Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

if not exist ".venv" (
    echo Installing virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt -q

echo.
echo Starting FastAPI on http://localhost:8000
echo Open http://localhost:8000 in your browser
echo Press Ctrl+C to stop.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

cd backend
python main.py
