## Offline Raspberry Pi 5 Assistant

Fully offline assistant for Raspberry Pi 5 (4GB) with three completely separated features:

- **Object detection** (K2)
- **Image capture** (K3 short press)
- **LLM chat (push‑to‑talk)** (K1 long press ≥ 1 s)

Always‑on robot eye animation runs in its own thread and pauses only while tasks are running, then returns to idle.

### Hardware

- **Board**: Raspberry Pi 5
- **Display**: 0.96" SSD1306 OLED (128x64, I²C)
- **Buttons (BCM, pull_up=True, active LOW)**:
  - **K1** → `GPIO17` (push‑to‑talk, long press ≥ 1 s)
  - **K2** → `GPIO27` (object detection)
  - **K3** → `GPIO22` (short press: capture image)
- **USB microphone**: audio input
- **USB speaker**: audio output
- **Camera**: PiCamera2

### Project structure

- **`main.py`**: boot, threads, event loop
- **`controller.py`**: routes button events to features (no cross‑feature calls)
- **`hardware/`**
  - **`buttons.py`**: GPIO polling in a single listener thread, emits events
  - **`oled.py`**: text + streaming token display
  - **`animation.py`**: robot eye animation (single 5s loop), separate thread
- **`audio/`**
  - **`recorder.py`**: push‑to‑talk recording via `sounddevice`
  - **`stt.py`**: offline STT using Vosk (`models/vosk/`)
  - **`tts.py`**: offline TTS using `espeak`
- **`ai/`**
  - **`llm.py`**: llama.cpp binding, loads `models/llm.gguf`, streams tokens
  - **`vision.py`**: Picamera2 capture and YOLOv8 detection (`models/yolo.pt`)
- **`storage/images/`**: saved captures
- **`scripts/download_models.py`**: helper to fetch GGUF, YOLO, and Vosk models

### Installation

From the `assistant/` folder:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv espeak portaudio19-dev libatlas-base-dev

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install rpi-lgpio
```

Enable camera and I²C in `raspi-config`, then reboot.

### Models (one‑time online step)

From `assistant/`:

```bash
source .venv/bin/activate
python scripts/download_models.py
```

This will:

- **Download LLM** to `models/llm.gguf` (TinyLlama chat GGUF – replace with any GGUF you prefer)
- **Download YOLOv8n** to `models/yolo.pt`
- **Download + unpack Vosk** English STT model into `models/vosk/`

You can swap in different GGUF / YOLO / Vosk models by overwriting these files/dirs.

### Running

```bash
cd assistant
source .venv/bin/activate
python main.py
```

On boot:

- **Robot eyes animation** starts on the OLED and loops:
  - center → slow left → center → slow right → blink (≈5 s loop)
- **Animation thread** is separate and continuously running.

### Controls and behavior

- **K2 (GPIO27) – Object detection**
  - Pauses animation
  - Captures a still image
  - Runs YOLOv8 (CPU) on the image
  - If an object is found:
    - Takes **first label** from YOLO result
    - Shows label on OLED
    - Speaks label via TTS
  - If no object:
    - Displays **"No object"**
    - Speaks fallback message
  - Returns to idle animation

- **K3 short (< 1 s) – Image capture**
  - Pauses animation
  - Captures an image
  - Saves it under `storage/images/capture_YYYYMMDD_HHMMSS.jpg`
  - Displays **"Image Saved"**
  - Returns to idle animation

- **K1 long (≥ 1 s) – LLM chat (push‑to‑talk)**
  - When press crosses 1 s:
    - Pauses animation
    - Clears OLED
    - Displays **"Listening..."**
    - Starts recording microphone audio
  - When button is released:
    - Stops recording
    - Runs offline STT (Vosk) on the WAV
    - Sends transcribed text to llama.cpp
    - Streams tokens **one‑by‑one** to the OLED using `show_streaming_text`
    - When generation finishes:
      - Speaks full response via TTS
      - Returns to idle animation

LLM chat is **single‑turn only** (no memory, no RAG).

### Threading model

- **Main thread**: runs `Controller.handle_event()`, performs all heavy work (YOLO, STT, LLM, TTS, camera)
- **Animation thread**: single dedicated thread in `AnimationManager.run()`
- **Button listener thread**: polls K1/K2/K3 and pushes events into a queue

No extra threads are created beyond these three.

### Error handling and safety

- All modules use **try/except** and log exceptions with `logging`
- Hardware failures (camera, OLED, microphone, models missing) do **not** crash the process
- On any feature failure, the controller calls `animation.resume()` and clears the OLED to return to idle
- Features are **strictly separated**:
  - Object detection never calls LLM or STT
  - Image capture never calls YOLO or LLM
  - Chat flow never calls object detection or image capture

### Customization notes

- To use a different GGUF, replace `models/llm.gguf` and adjust `ai/llm.py` if needed.
- To use a different YOLOv8 model, drop it as `models/yolo.pt`.
- To use a different Vosk language, unpack its model into `models/vosk/`.

