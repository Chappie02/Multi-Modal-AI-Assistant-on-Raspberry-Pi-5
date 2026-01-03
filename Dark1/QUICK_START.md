# Quick Start Guide

## 🚀 Fast Setup (5 Minutes)

### 1. Run Setup Script
```bash
sudo bash setup.sh
```

### 2. Download Models

**LLM Model:**
```bash
cd models
wget https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-q4_k_m.gguf
cd ..
```

**Vosk STT Model:**
```bash
cd ~
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
# Update path in main.py or move to project directory
```

### 3. Enable Hardware
```bash
sudo raspi-config
# Enable SPI and Camera
```

### 4. Test Components
```bash
sudo python3 test_components.py
```

### 5. Run Assistant
```bash
source venv/bin/activate
sudo python3 main.py
```

## 🎤 Usage

1. **Wake Word**: Say "Hey Pi" (or configure custom)
2. **Ask Question**: "What is the capital of France?"
3. **Object Detection**: Say "what is this?"
4. **Mode Switch**: "Switch to chat mode"

## 🔧 Common Issues

**LCD Not Working:**
- Check wiring
- Verify SPI enabled: `lsmod | grep spi`
- Must run with `sudo`

**Camera Not Working:**
- Enable in `raspi-config`
- Test: `libcamera-hello`

**Out of Memory:**
- Use smaller model (2B instead of 4B)
- Reduce context window in `llm_engine.py`

**Audio Not Working:**
- List devices: `arecord -l` and `aplay -l`
- Set default in `/etc/asound.conf`

## 📁 Project Structure

```
Dark1/
├── main.py              # Main entry point
├── test_components.py  # Component tests
├── setup.sh            # Setup script
├── requirements.txt    # Dependencies
│
├── core/               # AI modules
│   ├── llm_engine.py
│   ├── rag_memory.py
│   └── mode_manager.py
│
├── audio/              # Audio processing
│   ├── wake_word.py
│   ├── stt.py
│   └── tts.py
│
├── vision/             # Computer vision
│   ├── camera.py
│   └── detector.py
│
└── display/            # LCD display
    ├── lcd_driver.py
    └── ui_renderer.py
```

## 📚 Documentation

- **ARCHITECTURE.md**: Detailed system design
- **README.md**: Full documentation
- **Module files**: Inline comments and docstrings

## 💡 Tips

- **Performance**: Use Q4_K_M quantization for balance
- **Memory**: 4GB Pi 5 works with 2B models
- **Speed**: YOLOv8n is fastest for object detection
- **Privacy**: Everything runs offline, no cloud services

## 🎯 Next Steps

1. Customize wake word (Porcupine)
2. Add home automation (MQTT)
3. Train custom object detection
4. Add multi-language support

