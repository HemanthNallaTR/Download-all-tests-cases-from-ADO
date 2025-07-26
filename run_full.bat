@echo off
echo ========================================
echo Azure DevOps Test Case Downloader
echo Full Mode - Separate Suite Files
echo ========================================
echo.
echo This will download ALL available information including:
echo - Test Case ID, Title, Test Steps
echo - Plan/Suite details, State, Priority
echo - Assignments, Dates, Automation Status
echo - Area Path, Iteration Path, Tags, etc.
echo.
echo Output: Individual Excel files for each suite
echo Directory: test_cases_by_suite\
echo.

:: Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please create a .env file with your Azure DevOps credentials.
    echo See .env.example for the required format.
    pause
    exit /b 1
)

echo Configuration:
echo - Plan ID: 1410043
echo - Suite Range: 1410044 to 1410100
echo - Mode: Full details (all columns)
echo - Output: Separate files per suite
echo.

echo Starting download...
python test_case_downloader.py --mode full --output separate

echo.
echo ========================================
echo Download Complete
echo ========================================
echo.
echo Check the 'test_cases_by_suite' directory for your files:
echo - TestCases_Plan1410043_SuiteXXXXXX_Full.xlsx (individual files)
echo - TestCases_Plan1410043_Summary_Full.xlsx (all combined)
echo.
echo Each file contains all available test case fields.
echo.

pause
