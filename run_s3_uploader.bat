@echo off
echo ========================================
echo S3 Test Case Uploader
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

echo Installing/upgrading required packages...
pip install -r requirements.txt

echo.
echo Starting S3 Test Case Uploader...
echo.

python s3_test_case_uploader.py

echo.
echo Upload process completed.
pause
