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

REM Check for OpenAI API key
if "%OPENAI_API_KEY%"=="" (
    echo.
    echo WARNING: OPENAI_API_KEY environment variable not set!
    echo Please set your OpenAI API key before running:
    echo set OPENAI_API_KEY=your_api_key_here
    echo.
)

REM Start the server
echo.
echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
python main.py
