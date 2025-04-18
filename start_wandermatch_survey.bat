@echo off
echo WanderMatch Survey Application
echo ============================
echo.

REM Store original PATH
set "ORIGINAL_PATH=%PATH%"

REM Check for specific conda environment
if exist "C:\Users\yongp\anaconda3\envs\myenv\python.exe" (
    echo Found conda environment at C:\Users\yongp\anaconda3\envs\myenv
    set "PYTHON_EXE=C:\Users\yongp\anaconda3\envs\myenv\python.exe"
    
    REM Add conda env paths to PATH
    set "PATH=C:\Users\yongp\anaconda3\envs\myenv;C:\Users\yongp\anaconda3\envs\myenv\Scripts;C:\Users\yongp\anaconda3\envs\myenv\Library\bin;%PATH%"
) else (
    REM Check if Python is installed
    where python >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo Error: Python not found! Please install Python 3.12+ and try again.
        pause
        exit /b 1
    )
    set "PYTHON_EXE=python"
)

echo.
echo This application will:
echo  1. Start the Flask backend server
echo  2. Open a test form in your browser
echo  3. Allow you to submit survey data
echo  4. Save responses to UserInfo_and_Match/survey_results
echo.
echo IMPORTANT: If the browser opens to the API health page instead of the form,
echo           manually open the test_survey_form.html file in your browser.
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

REM Run the survey launcher script
echo.
echo Launching survey application...
echo.

"%PYTHON_EXE%" start_survey.py
set PYTHON_EXIT_CODE=%ERRORLEVEL%

REM Restore original PATH
set "PATH=%ORIGINAL_PATH%"

REM If there was an error, pause to show the message
if %PYTHON_EXIT_CODE% neq 0 (
    echo.
    echo An error occurred while running the survey (exit code: %PYTHON_EXIT_CODE%).
    echo.
    echo If this is your first time running the application,
    echo make sure that your environment has these requirements:
    echo  - Python 3.12+ with Flask, Flask-CORS, pandas, and requests packages
    echo  - Internet connection to load the browser interface
    echo.
    pause
) 