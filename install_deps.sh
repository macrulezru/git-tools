#!/bin/bash
# Установка зависимостей для Linux

echo "Установка зависимостей для Git Branch Manager..."

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python3 не установлен"
    echo "Установите Python3 с помощью менеджера пакетов вашего дистрибутива"
    echo "Например, для Ubuntu/Debian: sudo apt install python3"
    exit 1
fi

# Проверка pip
if ! command -v pip3 &> /dev/null; then
    echo "pip3 не установлен, устанавливаем..."
    sudo apt install python3-pip -y
fi

# Проверка git
if ! command -v git &> /dev/null; then
    echo "Git не установлен, устанавливаем..."
    sudo apt install git -y
fi

# Установка Python-пакетов
echo "Установка Python-пакетов..."
pip3 install --upgrade pip
pip3 install rich

# Для систем, где readline не установлен по умолчанию
if ! python3 -c "import readline" &> /dev/null; then
    echo "Установка readline..."
    sudo apt install python3-readline -y
fi

echo "Все зависимости успешно установлены!"
echo "Теперь вы можете запустить программу командой: python3 git_tools.py"