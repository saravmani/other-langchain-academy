@echo off
echo Starting Research Agent API...
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Check for Groq API key
if "%GROQ_API_KEY%"=="" (
    echo.
    echo WARNING: GROQ_API_KEY environment variable not set!
    echo Please set your Groq API key before running:
    echo set GROQ_API_KEY=your_groq_api_key_here
    echo.
)

REM Start the server
echo.
echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
python main.py
