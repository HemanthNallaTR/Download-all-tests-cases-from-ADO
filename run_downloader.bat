@echo off
echo Azure DevOps Test Case Downloader
echo ===================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if setup has been run
if not exist ".env" (
    echo Running initial setup...
    python setup.py
    if errorlevel 1 (
        echo Setup failed. Please fix the issues and try again.
        pause
        exit /b 1
    )
    echo.
)

REM Validate configuration
echo Validating configuration...
python validate_config.py
if errorlevel 1 (
    echo Configuration validation failed. Please fix the issues and try again.
    pause
    exit /b 1
)

echo.
echo Starting test case download...
echo.

REM Run the main script
python test_case_downloader.py

if errorlevel 1 (
    echo.
    echo Download failed. Check the logs above for details.
    pause
    exit /b 1
) else (
    echo.
    echo Download completed successfully!
    echo Check the generated Excel file for your test cases.
    
    REM Try to open the Excel file if it exists
    if exist "test_cases_export.xlsx" (
        echo.
        echo Opening Excel file...
        start "" "test_cases_export.xlsx"
    )
)

pause
