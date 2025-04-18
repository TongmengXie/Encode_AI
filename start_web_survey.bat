@echo off
echo ===================================
echo WanderMatch Web Survey Launcher
echo ===================================
echo.

:: Store original PATH to restore it later
set ORIGINAL_PATH=%PATH%

:: Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not found in your system PATH.
    echo Please install Python 3.8 or newer from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: Try to use Python from conda environment if available
set PYTHON_EXE=python
if exist "C:\Users\%USERNAME%\anaconda3\envs\myenv\python.exe" (
    set PYTHON_EXE=C:\Users\%USERNAME%\anaconda3\envs\myenv\python.exe
    echo Using Python from conda environment...
)

echo Starting WanderMatch Web Survey...
echo This will start both the frontend and backend servers and open your web browser.
echo.
echo IMPORTANT: For embedding calculation to work, you need to:
echo 1. Edit the .env file in the project root directory
echo 2. Set your OpenAI API key in the OPENAI_API_KEY variable
echo.
echo The frontend will be available at: http://localhost:8000/survey_launcher.html
echo The backend API will be running at: http://localhost:5000
echo.
echo Press Ctrl+C in the console to stop the servers when you're done.
echo.

:: Run the server script
cd "%~dp0"
"%PYTHON_EXE%" serve_survey.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Failed to run the WanderMatch Web Survey.
    echo.
    echo Please ensure you have:
    echo - Python 3.8 or newer installed
    echo - Required Python packages (flask, flask-cors, pandas, python-dotenv, openai)
    echo - An active internet connection
    echo - OpenAI API key in .env file for embedding calculation
    echo.
    pause
)

:: Restore original PATH
set PATH=%ORIGINAL_PATH% 