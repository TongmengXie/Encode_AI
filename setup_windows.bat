@echo off
REM setup_windows.bat - Windows version of the setup script for Render deployment

echo Setting up WanderMatch for Render deployment (Windows version)...

REM Create required directories
if not exist "UserInfo_and_Match\survey_results" (
    mkdir "UserInfo_and_Match\survey_results"
    echo Created directory: UserInfo_and_Match\survey_results
)

if not exist "wandermatch_output\maps" (
    mkdir "wandermatch_output\maps"
    echo Created directory: wandermatch_output\maps
)

if not exist "wandermatch_output\blogs" (
    mkdir "wandermatch_output\blogs"
    echo Created directory: wandermatch_output\blogs
)

REM Test directory permissions
echo Testing directory permissions...
set TEST_FILE=UserInfo_and_Match\survey_results\test_write.txt
echo Write test > "%TEST_FILE%"
if exist "%TEST_FILE%" (
    echo Successfully created test file
    del "%TEST_FILE%"
    echo Successfully removed test file
    echo Directory permissions look good!
) else (
    echo WARNING: Could not create test file. Check permissions manually.
)

REM Copy survey HTML files to the frontend public directory
echo Copying HTML files to frontend directory...
if not exist "deploy\frontend\public" (
    mkdir "deploy\frontend\public"
    echo Created directory: deploy\frontend\public
)

if exist "test_survey_form.html" (
    copy "test_survey_form.html" "deploy\frontend\public\" > nul
    echo Copied test_survey_form.html
) else (
    echo Warning: test_survey_form.html not found
)

if exist "survey_launcher.html" (
    copy "survey_launcher.html" "deploy\frontend\public\" > nul
    echo Copied survey_launcher.html
) else (
    echo Warning: survey_launcher.html not found
)

echo.
echo Setup complete!
echo Note: This is only for local testing. The main setup_render.sh will be used on Render.
echo.

pause 