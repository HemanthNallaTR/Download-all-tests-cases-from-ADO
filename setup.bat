@echo off
echo ========================================
echo Azure DevOps Test Case Downloader Setup
echo Initial Configuration and Dependency Installation
echo ========================================
echo.
echo This will:
echo 1. Check Python version compatibility
echo 2. Install required Python packages
echo 3. Create .env configuration file
echo 4. Test Azure DevOps connectivity
echo 5. Verify test plan access
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again.
    echo Download from: https://python.org/downloads/
    pause
    exit /b 1
)

echo Running setup script...
echo.

python setup.py

echo.
echo ========================================
echo Setup Complete
echo ========================================
echo.
echo If setup was successful, you can now use:
echo - run_essential.bat (essential columns only)
echo - run_full.bat (all columns)
echo - run_complete_workflow.bat (download + upload)
echo.

pause
