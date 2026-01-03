# Raspberry Pi 5 Multimodal LLM Assistant

A production-grade embedded AI assistant running entirely offline on Raspberry Pi 5. This system integrates voice interaction, computer vision, local LLM inference, and a custom LCD display to create an intelligent multimodal assistant.

## 🎯 Features

- **Voice Interaction**: Offline speech-to-text and text-to-speech
- **Local LLM**: Gemma-3-4B-IT running via llama.cpp
- **Object Detection**: YOLOv8 real-time object detection
- **RAG Memory**: Semantic search and conversation context
- **LCD Display**: Token-by-token streaming on 1.83" SPI LCD
- **Wake Word**: Hands-free activation
- **Dual Modes**: Chat mode and Object Detection mode

## 📋 Hardware Requirements

### Required Components

- **Raspberry Pi 5** (4GB+ RAM recommended)
- **Waveshare 1.83-inch LCD Module Rev2** (ST7789P controller)
- **Raspberry Pi Camera** (Picamera2 compatible)
- **Microphone** (USB or Bluetooth)
- **Speaker** (USB or Bluetooth)
- **MicroSD Card** (32GB+, Class 10+)

### LCD Wiring

| LCD Pin | Raspberry Pi Connection |
|---------|------------------------|
| VCC     | 3.3V                   |
| GND     | GND                    |
| DIN     | GPIO10 (Pin 19)        |
| CLK     | GPIO11 (Pin 23)        |
| CS      | GPIO8 / CE0 (Pin 24)   |
| DC      | GPIO25 (Pin 22)        |
| RST     | GPIO27 (Pin 13)        |
| BL      | GPIO18 (Pin 12)        |

## 🚀 Installation

### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-dev python3-venv \
    python3-rpi.gpio python3-picamera2 \
    espeak espeak-data libespeak1 libespeak-dev \
    portaudio19-dev libasound2-dev \
    libopenblas-dev liblapack-dev \
    build-essential cmake

# Enable SPI and camera
sudo raspi-config
# Navigate to: Interface Options > SPI > Enable
# Navigate to: Interface Options > Camera > Enable
```

### 2. Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip (reduces build issues)
pip install --upgrade pip setuptools wheel

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Download Models

#### LLM Model (Gemma-3-4B-IT)

```bash
# Create models directory
mkdir -p models

# Download Gemma-2-2B-IT GGUF (lighter alternative for Pi 5)
# Or Gemma-3-4B-IT if you have 8GB RAM
cd models
wget https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-q4_k_m.gguf
cd ..
```

#### YOLO Model

The YOLOv8n model will be downloaded automatically on first run by ultralytics.

#### STT Model (Vosk)

```bash
# Download Vosk English model
cd ~
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 /path/to/project/
```

### 4. Configure Paths

Edit `main.py` and update model paths if needed:

```python
# In main.py, update these paths:
self.llm = LLMEngine(
    model_path="models/gemma-2-2b-it-q4_k_m.gguf",  # Update if different
    ...
)

self.stt = SpeechToText(
    model_path="vosk-model-small-en-us-0.15",  # Update path
    ...
)
```

## 🎮 Usage

### Running the Assistant

```bash
# Must run with sudo for GPIO/SPI access
sudo python3 main.py
```

### Voice Commands

**Wake Word Activation:**
- Say "Hey Pi" to activate (or configure custom wake word)

**Chat Mode:**
- After wake word, ask questions naturally
- Example: "What is the capital of France?"
- Example: "Tell me a joke"

**Object Detection Mode:**
- Say "what is this?" or "detect objects"
- System captures image and identifies objects
- LLM explains detected objects naturally

**Mode Switching:**
- "Switch to chat mode"
- "Switch to object detection mode"

### LCD Display States

- **Idle**: Robot eyes animation
- **Listening**: Pulsing green circle
- **Thinking**: Rotating spinner
- **Speaking**: Token-by-token text display
- **Detecting**: Camera icon with "Detecting..." text

## 🏗️ Architecture

```
main.py (Orchestrator)
│
├── core/
│   ├── llm_engine.py      # llama.cpp integration
│   ├── rag_memory.py      # Vector store, semantic search
│   └── mode_manager.py    # Mode switching
│
├── audio/
│   ├── wake_word.py       # Keyword spotting
│   ├── stt.py             # Speech-to-text
│   └── tts.py             # Text-to-speech
│
├── vision/
│   ├── camera.py          # Picamera2 wrapper
│   └── detector.py        # YOLO object detection
│
└── display/
    ├── lcd_driver.py      # ST7789P SPI driver
    └── ui_renderer.py     # Token streaming, UI states
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.

## 🔧 Configuration

### Performance Tuning

**LLM Settings** (`core/llm_engine.py`):
```python
n_ctx=2048          # Context window (reduce for less RAM)
n_threads=4         # CPU threads (adjust for your Pi)
temperature=0.7      # Creativity (0.0-1.0)
```

**YOLO Settings** (`vision/detector.py`):
```python
model_path="yolov8n.pt"  # Use 'nano' for speed
confidence_threshold=0.25  # Lower = more detections
```

**LCD Settings** (`display/lcd_driver.py`):
```python
SPI_MAX_SPEED=40000000  # Reduce if unstable
```

### Memory Optimization

For Pi 5 with 4GB RAM:
- Use Gemma-2-2B instead of Gemma-3-4B
- Reduce LLM context window to 1024
- Use Q4_K_M quantization (not Q8)
- Limit RAG context retrieval (top_k=2)

## 🐛 Troubleshooting

### LCD Not Displaying

1. Check wiring connections
2. Verify SPI is enabled: `lsmod | grep spi`
3. Test SPI: `sudo python3 -c "import spidev; s=spidev.SpiDev(); s.open(0,0); print('SPI OK')"`
4. Check permissions: must run with `sudo`

### Camera Not Working

1. Enable camera: `sudo raspi-config`
2. Test: `libcamera-hello --list-cameras`
3. Check permissions: user must be in `video` group

### Audio Issues

1. List audio devices: `arecord -l` and `aplay -l`
2. Set default device in `/etc/asound.conf` if needed
3. Test microphone: `arecord -d 5 test.wav && aplay test.wav`

### LLM Too Slow

1. Use smaller model (2B instead of 4B)
2. Use lower quantization (Q4 instead of Q8)
3. Reduce context window
4. Close other applications

### Out of Memory

1. Enable swap: `sudo dphys-swapfile swapon`
2. Use smaller models
3. Reduce batch sizes
4. Close unnecessary services

## 📝 Development

### Project Structure

```
Dark1/
├── main.py                 # Main orchestrator
├── requirements.txt        # Python dependencies
├── ARCHITECTURE.md         # System design docs
├── README.md              # This file
│
├── core/                  # Core AI modules
│   ├── __init__.py
│   ├── llm_engine.py
│   ├── rag_memory.py
│   └── mode_manager.py
│
├── audio/                 # Audio processing
│   ├── __init__.py
│   ├── wake_word.py
│   ├── stt.py
│   └── tts.py
│
├── vision/                # Computer vision
│   ├── __init__.py
│   ├── camera.py
│   └── detector.py
│
└── display/               # LCD display
    ├── __init__.py
    ├── lcd_driver.py
    └── ui_renderer.py
```

### Adding Features

1. **Custom Wake Word**: Create Porcupine model at [Picovoice Console](https://console.picovoice.ai/)
2. **Home Automation**: Add MQTT client in `core/` directory
3. **Multi-language**: Update STT/TTS models and prompts
4. **Voice Cloning**: Integrate Coqui TTS for custom voices

## 📄 License

This project is provided as-is for educational and development purposes.

## 🙏 Acknowledgments

- llama.cpp for efficient LLM inference
- Ultralytics for YOLOv8
- Vosk for offline STT
- Waveshare for LCD hardware

## 📧 Support

For issues and questions:
1. Check [ARCHITECTURE.md](ARCHITECTURE.md) for system details
2. Review troubleshooting section above
3. Check component-specific documentation in module files

---

**Note**: This is a production-grade implementation designed for embedded AI engineers. All modules are well-commented and interview-ready.

