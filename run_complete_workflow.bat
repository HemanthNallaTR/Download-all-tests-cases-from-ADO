@echo off
echo ========================================
echo Complete Azure DevOps Workflow
echo Auto Mode - Essential + Upload
echo ========================================
echo.
echo This will run the complete workflow with default options:
echo - Download: Essential mode (4 columns only)
echo - Output: Separate files per suite  
echo - Upload: All files to Open Arena Chain
echo - File Management: Delete existing files before upload
echo.
echo The only prompt will be for TR Bearer Token if not in .env
echo.

:: Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please create a .env file with your Azure DevOps credentials.
    echo See .env.example for the required format.
    pause
    exit /b 1
)

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again.
    pause
    exit /b 1
)

echo Configuration:
echo - Plan ID: 1410043
echo - Suite Range: 1410044 to 1410100
echo - Mode: Essential (4 columns only)
echo - Output: Separate files per suite
echo - Upload: Auto-upload all files with defaults
echo.

echo ========================================
echo STEP 1: Downloading Test Cases
echo ========================================
echo.
echo Starting download with essential columns only...
python test_case_downloader.py --mode essential --output separate

:: Check if download was successful
if errorlevel 1 (
    echo.
    echo ❌ Download failed. Cannot proceed with upload.
    echo Please check the error messages above and try again.
    pause
    exit /b 1
)

echo.
echo ✅ Download completed successfully!
echo.

echo ========================================
echo STEP 2: Uploading to Open Arena Chain
echo ========================================
echo.
echo Starting upload with default options...
echo - Delete existing files: YES (default)
echo - Upload all files: YES (default)
echo - Only prompt: TR Bearer Token (if not in .env)
echo.

:: Run the automated uploader
python automated_uploader.py

:: Store the exit code
set UPLOAD_EXIT_CODE=%errorlevel%

:: Check upload result
if %UPLOAD_EXIT_CODE% neq 0 (
    echo.
    echo ❌ Upload failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 🎉 COMPLETE WORKFLOW FINISHED! 🎉
echo ========================================
echo.
echo ✅ Step 1: Test cases downloaded successfully
echo ✅ Step 2: All files uploaded to Open Arena Chain
echo.
echo 📁 Downloaded files location: test_cases_by_suite\
echo 🌐 Files are now available in your Open Arena Chain workspace
echo.
echo Workflow completed with all default options:
echo - Essential columns only (ID, Title, Steps, Expected Results)
echo - Separate files per test suite
echo - All existing files deleted before upload
echo - All new files uploaded automatically
echo.

pause
