#!/bin/bash
# Dependency installation for Linux

echo "Installing dependencies for Git Branch Manager..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed"
    echo "Install Python3 using your distribution's package manager"
    echo "For Ubuntu/Debian: sudo apt install python3"
    exit 1
fi

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed, installing..."
    sudo apt install python3-pip -y
fi

# Check git
if ! command -v git &> /dev/null; then
    echo "Git is not installed, installing..."
    sudo apt install git -y
fi

# Install Python packages
echo "Installing Python packages..."
pip3 install --upgrade pip
pip3 install rich

# For systems where readline is not installed by default
if ! python3 -c "import readline" &> /dev/null; then
    echo "Installing readline..."
    sudo apt install pyreadline3 -y
fi

echo "All dependencies installed successfully!"
echo "You can now run the program with: python3 git_tools.py"