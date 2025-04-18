@echo off
:: Установка зависимостей для Windows
echo Установка зависимостей для Git Branch Manager...

:: Проверка Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Ошибка: Python не установлен или не добавлен в PATH
    echo Пожалуйста, установите Python 3.x с https://www.python.org/
    pause
    exit /b 1
)

:: Проверка pip
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Ошибка: pip не установлен
    echo Попробуйте переустановить Python с опцией "Add Python to PATH"
    pause
    exit /b 1
)

:: Проверка git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Ошибка: Git не установлен
    echo Пожалуйста, установите Git с https://git-scm.com/
    pause
    exit /b 1
)

:: Установка Python-пакетов
echo Установка Python-пакетов...
python -m pip install --upgrade pip
python -m pip install rich pyreadline

echo Все зависимости успешно установлены!
echo Теперь вы можете запустить программу командой: python git_tools.py
pause