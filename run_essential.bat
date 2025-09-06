@echo off
echo ========================================
echo Azure DevOps Test Case Downloader
echo Essential Mode - Separate Suite Files
echo ========================================
echo.
echo This will download ONLY essential information:
echo - Test Case ID
echo - Title  
echo - Test Steps
echo - Expected Results
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
echo - Mode: Essential columns only
echo - Output: Separate files per suite
echo.

echo Starting download...
python test_case_downloader.py --mode essential --output separate

echo.
echo ========================================
echo Download Complete
echo ========================================
echo.
echo Check the 'test_cases_by_suite' directory for your files:
echo - TestCases_Plan1410043_SuiteXXXXXX_Essential.xlsx (individual files)
echo - TestCases_Plan1410043_Summary_Essential.xlsx (all combined)
echo.
echo Each file contains only 4 columns:
echo 1. Test Case ID
echo 2. Title
echo 3. Test Steps  
echo 4. Expected Results
echo.

pause
