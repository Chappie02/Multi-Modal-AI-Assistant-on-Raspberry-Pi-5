#!/usr/bin/env python3
"""
Setup script for Raspberry Pi 5 Offline AI Assistant
This script helps with initial setup and dependency installation.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_system():
    """Check if running on Raspberry Pi."""
    print("🔍 Checking system...")
    
    # Check if running on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo:
                print("✅ Raspberry Pi detected")
                return True
    except:
        pass
    
    print("⚠️  Not running on Raspberry Pi - some features may not work correctly")
    return False


def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    directories = [
        'models',
        'chroma_db',
        'temp'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")


def install_system_dependencies():
    """Install system dependencies."""
    print("📦 Installing system dependencies...")
    
    commands = [
        ("sudo apt update", "Updating package list"),
        ("sudo apt install -y python3-pip python3-venv python3-opencv", "Installing Python and OpenCV"),
        ("sudo apt install -y libhdf5-dev libhdf5-serial-dev", "Installing HDF5 libraries"),
        ("sudo apt install -y libatlas-base-dev libjasper-dev", "Installing additional libraries"),
        ("sudo apt install -y libqtgui4 libqt4-test libqtwebkit4", "Installing Qt libraries"),
        ("sudo apt install -y libgtk-3-dev libavcodec-dev libavformat-dev", "Installing multimedia libraries"),
        ("sudo apt install -y libswscale-dev libv4l-dev libxvidcore-dev libx264-dev", "Installing video libraries")
    ]
    
    success_count = 0
    for command, description in commands:
        if run_command(command, description):
            success_count += 1
    
    print(f"📊 System dependencies: {success_count}/{len(commands)} installed successfully")
    return success_count == len(commands)


def setup_virtual_environment():
    """Setup Python virtual environment."""
    print("🐍 Setting up Python virtual environment...")
    
    if not Path('venv').exists():
        if run_command('python3 -m venv venv', 'Creating virtual environment'):
            print("✅ Virtual environment created")
        else:
            return False
    else:
        print("✅ Virtual environment already exists")
    
    # Activate virtual environment and install requirements
    pip_commands = [
        'source venv/bin/activate && pip install --upgrade pip',
        'source venv/bin/activate && pip install -r requirements.txt'
    ]
    
    for command in pip_commands:
        if not run_command(command, 'Installing Python packages'):
            return False
    
    return True


def download_models():
    """Download required AI models."""
    print("🤖 Setting up AI models...")
    
    # YOLOv8 will be downloaded automatically on first run
    print("✅ YOLOv8 model will be downloaded automatically")
    
    # Check for LLaMA model
    llama_paths = [
        'models/llama-7b-q4_0.gguf',
        'models/llama-7b.gguf',
        'models/llama-2-7b-chat.Q4_0.gguf'
    ]
    
    llama_found = False
    for path in llama_paths:
        if Path(path).exists():
            print(f"✅ LLaMA model found: {path}")
            llama_found = True
            break
    
    if not llama_found:
        print("⚠️  LLaMA model not found!")
        print("Please download a GGUF quantized LLaMA model and place it in the models/ directory")
        print("Recommended: llama-2-7b-chat.Q4_0.gguf")
        print("You can download from: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF")
    
    return llama_found


def enable_camera():
    """Provide instructions for enabling camera."""
    print("📷 Camera setup instructions:")
    print("1. Run: sudo raspi-config")
    print("2. Navigate to: Interface Options > Camera")
    print("3. Select: Enable")
    print("4. Reboot: sudo reboot")
    print("5. Test camera: python -c \"import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())\"")


def main():
    """Main setup function."""
    print("🚀 Raspberry Pi 5 Offline AI Assistant Setup")
    print("=" * 50)
    
    # Check system
    is_pi = check_system()
    
    # Create directories
    create_directories()
    
    # Install system dependencies (only on Raspberry Pi)
    if is_pi:
        install_system_dependencies()
    
    # Setup virtual environment
    if not setup_virtual_environment():
        print("❌ Failed to setup virtual environment")
        return False
    
    # Download models
    download_models()
    
    # Camera instructions
    if is_pi:
        enable_camera()
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Download a LLaMA model if not already done")
    print("2. Enable camera interface (if on Raspberry Pi)")
    print("3. Run: python main.py")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
