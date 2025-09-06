@echo off
echo Azure DevOps Test Case Downloader - Quick Start
echo =================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

echo Step 1: Installing minimal dependencies...
python -m pip install requests python-dotenv --prefer-binary --quiet

echo Step 2: Creating environment file...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo Created .env file from template
        echo.
        echo IMPORTANT: Please edit .env file with your Azure DevOps credentials:
        echo   - AZURE_DEVOPS_ORG_URL
        echo   - AZURE_DEVOPS_PAT (Personal Access Token)
        echo   - AZURE_DEVOPS_DEFAULT_PROJECT
        echo.
        echo Press any key when you've updated the .env file...
        pause >nul
    ) else (
        echo Error: .env.example file not found
        pause
        exit /b 1
    )
)

echo Step 3: Running lightweight downloader (CSV export)...
echo This version avoids Excel dependencies that can cause installation issues.
echo.

python lightweight_downloader.py

if errorlevel 1 (
    echo.
    echo Download failed. Please check the error messages above.
    pause
    exit /b 1
) else (
    echo.
    echo Download completed successfully!
    echo.
    echo Files created:
    echo   - test_cases_export.csv (Standard CSV)
    echo   - test_cases_export_excel.csv (Excel-compatible CSV)
    echo.
    echo You can open the Excel-compatible CSV file in Excel or any spreadsheet application.
    echo.
    
    REM Try to open the CSV file
    if exist "test_cases_export_excel.csv" (
        echo Opening CSV file...
        start "" "test_cases_export_excel.csv"
    )
)

pause
