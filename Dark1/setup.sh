#!/bin/bash
# Setup script for Raspberry Pi 5 Multimodal LLM Assistant
# Run with: bash setup.sh

set -e

echo "=========================================="
echo "Raspberry Pi 5 Multimodal LLM Assistant"
echo "Setup Script"
echo "=========================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if running as root for system packages
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo) for system package installation"
    echo "Usage: sudo bash setup.sh"
    exit 1
fi

echo "Step 1: Updating system packages..."
apt update && apt upgrade -y

echo ""
echo "Step 2: Installing system dependencies..."
apt install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    python3-rpi.gpio \
    python3-picamera2 \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    portaudio19-dev \
    libasound2-dev \
    libopenblas-dev \
    liblapack-dev \
    build-essential \
    cmake \
    git \
    wget \
    unzip

echo ""
echo "Step 3: Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo ""
echo "Step 4: Activating virtual environment and upgrading pip..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel

echo ""
echo "Step 5: Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "Step 6: Creating directories..."
mkdir -p models
mkdir -p logs

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Download LLM model:"
echo "   cd models"
echo "   wget https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-q4_k_m.gguf"
echo ""
echo "2. Download Vosk STT model:"
echo "   cd ~"
echo "   wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
echo "   unzip vosk-model-small-en-us-0.15.zip"
echo "   mv vosk-model-small-en-us-0.15 /path/to/project/"
echo ""
echo "3. Enable SPI and Camera:"
echo "   sudo raspi-config"
echo "   -> Interface Options -> SPI -> Enable"
echo "   -> Interface Options -> Camera -> Enable"
echo ""
echo "4. Run the assistant:"
echo "   source venv/bin/activate"
echo "   sudo python3 main.py"
echo ""
echo "Note: Script must run with sudo for GPIO/SPI access"
echo ""

