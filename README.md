# Multi-Modal-AI-Assistant-on-Raspberry-Pi-5

**Local LLM + YOLO + RAG Memory + 0.96" OLED + Voice Interface
Fully Offline | Raspberry Pi 5 | Hardware-Controlled | Edge AI System**

A fully offline, embedded multimodal AI assistant built on the Raspberry Pi 5 that integrates real-time object detection, local large language model conversation, retrieval-augmented memory, voice interaction, and a hardware OLED user interface — all controlled entirely through physical buttons.

This system runs without any cloud APIs, external servers, or terminal interaction. Everything operates locally on-device.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Hardware Requirements](#hardware-requirements)
- [Hardware Wiring](#hardware-wiring)
  - [OLED Display (SSD1306 0.96" I2C)](#oled-display-ssd1306-096-i2c)
  - [Buttons (K1, K2, K3)](#push-buttons-k1-k2-k3)
- [speed switch Push Button Controls](#button-controls)
- [Operating Modes](#operating-modes)
  - [LLM Conversation Mode (K1)](#llm-conversation-mode-k1)
  - [Object Detection Mode (K2)](#object-detection-mode-k2)
  - [Image Capture Mode (K3)](#image-capture-mode-k3)
- [Project Structure](#project-structure)
- [Installation](#installation)
  - [1. System Dependencies](#1-system-dependencies)
  - [2. Virtual Environment Setup](#2-virtual-environment-setup)
  - [3. Python Requirements](#3-python-requirements)
  - [4. Model Downloads](#4-model-downloads)
  - [5. Hardware Interface Configuration](#5-hardware-interface-configuration)
- [Usage](#usage)
- [Screenshots](#Screenshots)
- [License](#license)

---

## System Architecture

```
+-----------------------------------------------------------------------+
|                        RASPBERRY PI 5 (4GB)                           |
|                                                                       |
|  +---------------------+    +--------------------------------------+  |
|  |   HARDWARE LAYER    |    |           SOFTWARE LAYER             |  |
|  |                     |    |                                      |  |
|  |  [K1] GPIO 17 ------+--->|  ButtonListener (polling, 10ms)      |  |
|  |  [K2] GPIO 27 ------+--->|       |                              |  |
|  |  [K3] GPIO 22 ------+--->|       v                              |  |
|  |                     |    |  EventQueue (thread-safe)            |  |
|  |  USB Microphone ----+--->|       |                              |  |
|  |  USB Speaker <------+----|       v                              |  |
|  |                     |    |  Controller (main thread)            |  |
|  |  Camera Module -----+--->|   |        |         |               |  |
|  |                     |    |   v        v         v               |  |
|  |  SSD1306 OLED <-----+----|  LLM    Vision    AudioRecorder      |  |
|  |  (I2C: SDA/SCL)     |    |  (llama  (YOLO    (sounddevice)      |  |
|  |                     |    |   .cpp)   v8n)      |                |  |
|  +---------------------+    |   |        |        v                |  |
|                             |   |        |     STT (Vosk)          |  |
|                             |   |        |        |                |  |
|                             |   v        v        v                |  |
|                             |  TTS (espeak) <-- response           |  |
|                             |                                      |  |
|                             |  RAG Memory                          |  |
|                             |   ChromaDB + sentence-transformers   |  |
|                             |   (all-MiniLM-L6-v2)                 |  |
|                             +--------------------------------------+  |
|                                                                       |
| +------------------------------------------------------------------+  |
| | THREADING MODEL                                                  |  |
| |  Thread 1: main        --> Controller.handle_event() loop        |  |
| |  Thread 2: animation   --> AnimationManager.run() (OLED eyes)    |  |
| |  Thread 3: buttons     --> ButtonListener.run() (GPIO polling)   |  |
| +------------------------------------------------------------------+  |
+-----------------------------------------------------------------------+
```

---

## Hardware Requirements

| Component               | Specification                     |
|-------------------------|-----------------------------------|
| Single-Board Computer   | Raspberry Pi 5 (4GB recommended)  |
| Operating System        | Raspberry Pi OS 64-bit (Bookworm) |
| Camera                  | Raspberry Pi Camera Module v2/v3  |
| Microphone              | USB microphone                    |
| Speaker                 | USB speaker or 3.5mm w/ USB DAC   |
| Display                 | 0.96 inch OLED display rotary encoder combination module|

---

## Hardware Wiring

### OLED Display (SSD1306 0.96" I2C)

The OLED communicates over the I2C bus. Connect to the Raspberry Pi 5 GPIO header as follows:

| OLED Pin | Function | RPi 5 Pin (Board) | RPi 5 Pin (BCM) |
|----------|----------|--------------------|------------------|
| VCC      | Power    | Pin 1              | 3.3V             |
| GND      | Ground   | Pin 6              | GND              |
| SCL      | Clock    | Pin 5              | GPIO 3 (SCL1)    |
| SDA      | Data     | Pin 3              | GPIO 2 (SDA1)    |

```
  SSD1306 OLED (Front)
  +------------------+
  |                  |
  |   128 x 64 px   |
  |                  |
  +--+-+-+-+---------+
     | | | |
    VCC GND SCL SDA
     |   |   |   |
     |   |   |   +---> RPi Pin 3  (GPIO 2 / SDA1)
     |   |   +-------> RPi Pin 5  (GPIO 3 / SCL1)
     |   +-----------> RPi Pin 6  (GND)
     +---------------> RPi Pin 1  (3.3V)
```

> **Note:** The software applies a 180-degree rotation to the display buffer by default (`rotate_180 = True` in `hardware/oled.py`). If the display appears inverted, set this flag to `False`.

### 3-speed switch Push Buttons (K1, K2, K3)

All buttons use BCM-numbered GPIO pins configured with internal pull-up resistors. Each button connects its respective GPIO pin to GND when pressed (active-low logic).

| Button | Function         | GPIO (BCM) | Board Pin |
|--------|------------------|------------|-----------|
| K1     | Push-to-Talk     | GPIO 17    | Pin 11    |
| K2     | Object Detection | GPIO 27    | Pin 13    |
| K3     | Image Capture    | GPIO 22    | Pin 15    |

---

## Button Controls

| Button | Action     | Behavior                                        |
|--------|------------|-------------------------------------------------|
| K1     | Hold >= 1s | Push-to-talk. Hold to record, release to submit |
| K2     | Press      | Capture image and run YOLOv8 object detection   |
| K3     | Press      | Capture image and save to local storage         |

All interactions are event-driven. The `ButtonListener` thread polls GPIO at 10ms intervals and pushes `ButtonEvent` objects into a thread-safe queue consumed by the `Controller` on the main thread.

---

## Operating Modes

### LLM Conversation Mode (K1)

1. User holds **K1** for at least 1 second to activate push-to-talk.
2. Audio is recorded via USB microphone using `sounddevice` (16kHz, mono).
3. On release, the audio buffer is written to a temporary WAV file.
4. **Vosk** performs offline speech-to-text transcription.
5. The transcribed text is sent to the **RAG retriever**, which queries ChromaDB for the top-3 most relevant context chunks (knowledge base entries and past conversations).
6. The augmented prompt (system + context + user query) is passed to **Gemma 3 4B** via `llama-cpp-python`.
7. Tokens stream to the OLED display in real time (word-wrapped, last 4 lines visible).
8. After generation completes, the full response is spoken aloud via **espeak**.
9. The question-answer pair is persisted into the RAG vector store for future retrieval.

If RAG initialization or retrieval fails at any point, the system falls back to plain LLM inference without interrupting the user experience.

### Object Detection Mode (K2)

1. User presses **K2**.
2. A still image is captured from the Pi Camera module.
3. **YOLOv8 Nano** runs inference on the captured frame.
4. The first detected object label is displayed on the OLED and spoken via TTS.
5. If no object is detected, "No object detected" is displayed and spoken.

### Image Capture Mode (K3)

1. User presses **K3** (short press, < 1 second).
2. A timestamped JPEG image is captured and saved to `storage/images/`.
3. Confirmation is displayed on the OLED.

---

## Project Structure

```
assistant/
|-- main.py                     # Application entry point; thread orchestration
|-- controller.py               # Central event handler and subsystem coordinator
|-- requirements.txt            # Python package dependencies
|
|-- ai/
|   |-- llm.py                  # LLM inference via llama-cpp-python (Gemma GGUF)
|   |-- vision.py               # Camera capture and YOLOv8 object detection
|
|-- audio/
|   |-- recorder.py             # Push-to-talk audio recording (sounddevice)
|   |-- stt.py                  # Offline speech-to-text (Vosk)
|   |-- tts.py                  # Offline text-to-speech (espeak)
|
|-- hardware/
|   |-- buttons.py              # GPIO button listener with debounce logic
|   |-- oled.py                 # SSD1306 OLED driver (I2C, 128x64)
|   |-- animation.py            # Idle eye animation loop for OLED
|
|-- rag/
|   |-- __init__.py
|   |-- embedder.py             # Sentence embedding (all-MiniLM-L6-v2)
|   |-- vector_store.py         # ChromaDB persistent vector store wrapper
|   |-- retriever.py            # RAG orchestration: indexing, retrieval, memory
|
|-- scripts/
|   |-- download_models.py      # Automated model downloader (LLM, YOLO, Vosk)
|
|-- data/
|   |-- knowledge_base/         # Plain text files for RAG indexing (.txt)
|
|-- models/                     # (created at runtime)
|   |-- gemma-3-4b-it-IQ4_XS.gguf
|   |-- yolo.pt
|   |-- vosk/
|
|-- storage/
|   |-- images/                 # Captured images from K2/K3 (created at runtime)
```

---

## Installation

All steps below assume a fresh Raspberry Pi OS 64-bit (Bookworm) installation on a Raspberry Pi 5.

### 1. System Dependencies

These must be installed **before** creating the virtual environment or installing Python packages. Several Python libraries depend on system-level C libraries and tools.

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
    python3-dev \
    python3-venv \
    python3-pip \
    python3-picamera2 \
    libcamera-dev \
    libcap-dev \
    espeak \
    libportaudio2 \
    portaudio19-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    i2c-tools \
    git \
    cmake \
    build-essential
```

Verify I2C detection after wiring the OLED:

```bash
sudo i2cdetect -y 1
```

The SSD1306 should appear at address `0x3C`.

### 2. Virtual Environment Setup

```bash
cd ~/Desktop/mark69/assistant

python3 -m venv venv --system-site-packages
source venv/bin/activate
```

> **Note:** The `--system-site-packages` flag is required to inherit `picamera2` and other system-installed packages that are not available via pip.

### 3. Python Requirements

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**`requirements.txt` contents:**

| Package                          | Purpose                                   |
|----------------------------------|-------------------------------------------|
| `llama-cpp-python`               | LLM inference (Gemma GGUF via llama.cpp)  |
| `ultralytics`                    | YOLOv8 object detection                   |
| `picamera2`                      | Raspberry Pi camera interface             |
| `sounddevice`                    | USB microphone audio capture              |
| `numpy`                          | Numerical operations                      |
| `Pillow`                         | Image processing and OLED rendering       |
| `adafruit-circuitpython-ssd1306` | SSD1306 OLED I2C driver                   |
| `RPi.GPIO`                       | GPIO pin access                           |
| `rpi-lgpio`                      | GPIO compatibility layer for Pi 5         |
| `vosk`                           | Offline speech-to-text                    |
| `chromadb`                       | Persistent vector database for RAG        |
| `sentence-transformers`          | Text embeddings (all-MiniLM-L6-v2)        |

> **Important:** `llama-cpp-python` compiles from source on ARM64. Expect the initial installation to take 10-15 minutes on a Raspberry Pi 5.

### 4. Model Downloads

The project includes an automated download script. Run it from within the activated virtual environment:

```bash
python scripts/download_models.py
```

This downloads three models into the `models/` directory:

| Model                            | File                             | Size   | Source                    |
|----------------------------------|----------------------------------|--------|---------------------------|
| Gemma 3 4B Instruct (IQ4_XS)    | `gemma-3-4b-it-IQ4_XS.gguf`     | ~2.3GB | Hugging Face (unsloth)    |
| YOLOv8 Nano                     | `yolo.pt`                        | ~6MB   | Ultralytics               |
| Vosk English (small)            | `vosk/` (extracted directory)    | ~40MB  | alphacephei.com           |

**To use a custom YOLO model** (e.g., a fine-tuned `best.pt`):

```bash
cp /path/to/your/best.pt models/yolo.pt
```

The `VisionSystem` class loads from `models/yolo.pt` by default.

The **sentence-transformers** embedding model (`all-MiniLM-L6-v2`) is downloaded automatically on first application launch via the `sentence_transformers` library.

### 5. Hardware Interface Configuration

Ensure I2C are enabled via `raspi-config`:

```bash
sudo raspi-config
```

Navigate to **Interface Options** and enable:
- I2C
- Camera (Legacy) -- if using Camera Module v2

Reboot after making changes:

```bash
sudo reboot
```

---

## Usage

```bash
cd ~/Desktop/mark69/assistant
source venv/bin/activate
python main.py
```

The system starts three concurrent threads:

1. **Animation thread** -- renders the idle eye animation on the OLED.
2. **Button listener thread** -- polls GPIO pins for K1/K2/K3 events.
3. **Main thread** -- processes button events through the `Controller`.

No terminal interaction is required after launch. All feedback is delivered through the OLED display and USB speaker.

## Performance Notes

| Metric                           | Approximate Value                |
|----------------------------------|----------------------------------|
| Cold boot to idle animation      | 15-25 seconds                    |
| LLM first-token latency         | 3-8 seconds                      |
| LLM token generation rate       | 5-10 tokens/second               |
| YOLOv8 Nano inference (first)   | 30+ seconds (model loading)      |
| YOLOv8 Nano inference (cached)  | 1-3 seconds                      |
| Vosk STT transcription          | Near real-time                   |
| RAG embedding + retrieval       | 0.5-2 seconds                    |
| OLED refresh rate               | ~20 FPS (animation loop)         |

- The Gemma 3 4B IQ4_XS quantization is selected specifically for the Pi 5's 4GB memory constraint. Peak RAM usage during LLM inference may reach 3.2-3.5 GB.
- The `n_ctx=2048` context window and `max_tokens=256` limits are tuned to balance response quality against memory and latency on ARM64.
- The RAG vector store uses a rolling window of 100 conversation entries to prevent unbounded disk and memory growth.
- The embedding model (`all-MiniLM-L6-v2`) is loaded once as a singleton and retained in memory for the process lifetime.
- YOLOv8 Nano is the smallest variant in the YOLO family; larger models (e.g., YOLOv8s, YOLOv8m) will exceed practical inference time on the Pi 5.


## Screenshots
<p align="left">
  <img src="https://github.com/user-attachments/assets/2211b823-ea61-4bdd-9bb5-43c0f1450c62" width="500">
</p>
<p align="left">
  <img src="https://github.com/user-attachments/assets/913da2bd-7748-4fc3-b378-35c95680a539" width="500">
</p>
<p align="left">
  <img src="https://github.com/user-attachments/assets/e21d83fe-214d-446e-8455-0748ebc4b440" width="500">
</p>

## License

Released under MIT License

Copyright (c) 2026 Suhas S Telkar
