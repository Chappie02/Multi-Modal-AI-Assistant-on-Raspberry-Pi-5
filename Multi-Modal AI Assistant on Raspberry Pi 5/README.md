# Raspberry Pi 5 Offline AI Assistant

A complete CLI-based Python application for a Raspberry Pi 5 that combines local large language models (LLM) with YOLOv8 object detection for an offline AI assistant experience.

## 🚀 Features

- **Chat Mode**: Text-based conversation using local LLM (llama.cpp)
- **Object Detection Mode**: Camera-based object detection with scene summarization
- **Fully Offline**: No internet connection required after setup
- **Raspberry Pi 5 Optimized**: Optimized for 4GB RAM Pi 5 with CPU-only inference
- **Modular Design**: Clean, extensible codebase with separate modules

## 📋 Requirements

### Hardware
- Raspberry Pi 5 (4GB RAM recommended)
- Raspberry Pi Camera Module (or USB camera)
- MicroSD card (32GB+ recommended)
- Power supply (5V, 3A recommended)

### Software
- Raspberry Pi OS (64-bit recommended)
- Python 3.8+
- OpenCV-compatible camera

## 🛠️ Installation

### 1. Clone or Download the Project
```bash
cd /home/pi
git clone <repository-url> ai_assistant
# OR download and extract the project files
```

### 2. Install System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3-pip python3-venv python3-opencv
sudo apt install -y libhdf5-dev libhdf5-serial-dev
sudo apt install -y libatlas-base-dev libjasper-dev libqtgui4 libqt4-test
sudo apt install -y libqtwebkit4 libgtk-3-dev libavcodec-dev libavformat-dev
sudo apt install -y libswscale-dev libv4l-dev libxvidcore-dev libx264-dev
```

### 3. Create Virtual Environment
```bash
cd ai_assistant
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Download AI Models

#### YOLOv8 Model
The YOLOv8 model will be downloaded automatically on first run.

#### LLaMA Model
Download a GGUF quantized LLaMA model (recommended: 7B q4_0):

```bash
# Create models directory
mkdir -p models

# Download LLaMA 7B q4_0 model (example URL - use actual download link)
cd models
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_0.gguf
# OR download from another source
```

### 6. Enable Camera
```bash
# Enable camera interface
sudo raspi-config
# Navigate to Interface Options > Camera > Enable
sudo reboot
```

## 🎯 Usage

### Starting the Application
```bash
cd ai_assistant
source venv/bin/activate
python main.py
```

### Available Commands

#### Main Menu
- `chat mode` - Enter text-based chat mode
- `object mode` - Enter camera-based object detection mode
- `exit` - Exit the application

#### Chat Mode Commands
- Type any message to chat with the local LLM
- `exit` - Return to main menu

#### Object Detection Mode Commands
- `what is this` - Capture image and analyze scene
- `exit` - Return to main menu

## 📁 Project Structure

```
ai_assistant/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── modes/                 # Application modes
│   ├── chat_mode.py       # Chat mode implementation
│   └── object_mode.py     # Object detection mode
├── utils/                 # Utility modules
│   ├── camera_utils.py    # Camera operations
│   ├── llm_utils.py       # LLM management
│   ├── rag_utils.py       # RAG functionality
│   └── system_utils.py    # System monitoring
├── models/                # AI model files
│   └── llama-7b-q4_0.gguf # LLaMA model (download separately)
└── chroma_db/             # RAG database (created automatically)
```

## ⚙️ Configuration

### Model Configuration
Edit the model paths in the respective mode files if your models are in different locations:

```python
# In chat_mode.py and object_mode.py
model_paths = [
    "./models/llama-7b-q4_0.gguf",  # Add your model path here
    "/home/pi/models/llama-7b.gguf",
    # ... other paths
]
```

### Camera Configuration
Adjust camera settings in `utils/camera_utils.py`:

```python
# Camera resolution and settings
resolution = (640, 480)  # Adjust as needed
camera_index = 0         # Camera device index
```

### Performance Tuning
Adjust LLM parameters in the mode files based on your system:

```python
# For systems with less RAM
n_ctx = 1024        # Context window
n_threads = 2       # CPU threads
max_tokens = 128    # Response length
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Camera Not Working
```bash
# Check if camera is detected
ls /dev/video*
# Test camera with OpenCV
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

#### 2. Model Loading Errors
- Ensure model files are in the correct directory
- Check file permissions
- Verify model format (GGUF files only)

#### 3. Memory Issues
- Reduce context window size (`n_ctx`)
- Close other applications
- Consider using smaller models

#### 4. Slow Performance
- Reduce camera resolution
- Lower YOLO confidence threshold
- Use fewer CPU threads for LLM

### Debug Mode
Enable debug output by setting environment variable:
```bash
export DEBUG=1
python main.py
```


