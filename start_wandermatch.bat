@echo off
echo ===================================
echo WanderMatch Application Launcher
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

:: Check if Node.js is installed
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Node.js is not found in your system PATH.
    echo Please install Node.js from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo Starting WanderMatch application...
echo This may take a moment to initialize both backend and frontend.
echo.

:: Run the deployment script
cd "%~dp0"
"%PYTHON_EXE%" deploy\run_deployment.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Failed to run the WanderMatch application.
    echo.
    echo Please ensure you have:
    echo - Python 3.8 or newer installed
    echo - Node.js and npm installed
    echo - An active internet connection
    echo.
    pause
)

:: Restore original PATH
set PATH=%ORIGINAL_PATH% 