@echo off
:: Dependency installation for Windows
echo Installing dependencies for Git Branch Manager...

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not added to PATH
    echo Please install Python 3.x from https://www.python.org/
    pause
    exit /b 1
)

:: Check pip
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: pip is not installed
    echo Try reinstalling Python with the "Add Python to PATH" option
    pause
    exit /b 1
)

:: Check git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Git is not installed
    echo Please install Git from https://git-scm.com/
    pause
    exit /b 1
)

:: Install Python packages
echo Installing Python packages...
python -m pip install --upgrade pip
python -m pip install rich pyreadline3

echo All dependencies installed successfully!
echo You can now run the program with: python git_tools.py
pause