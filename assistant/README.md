## Raspberry Pi 5 Offline Multimodal Assistant (OLED + Buttons)

Fully offline, Raspberry Pi 5 (4GB) multimodal assistant with a CLI backend and SSD1306 OLED frontend.

- **K1**: push‑to‑talk LLM conversation (offline STT → RAG → llama.cpp → OLED stream → offline TTS)
- **K2**: object detection (camera + YOLO)
- **K3**: capture image and store to disk

**Important design rule**: features are strictly separated (chat never calls vision; vision never calls LLM).

---

### Hardware

- **Board**: Raspberry Pi 5
- **Display**: 0.96" SSD1306 OLED (128x64, I²C)
- **Buttons (BCM, pull‑up, active LOW)**:
  - **K1** → `GPIO17` (push‑to‑talk, long press ≥ 1s)
  - **K2** → `GPIO27` (object detection)
  - **K3** → `GPIO22` (short press: capture image)
- **USB microphone**: audio input
- **USB speaker**: audio output
- **Camera**: PiCamera2

---

### What’s offline vs online

- **Offline at runtime**: STT (Vosk), embeddings (SentenceTransformers), vector DB (ChromaDB), LLM inference (llama.cpp via `llama-cpp-python`), TTS (`espeak`), OLED UI.
- **One‑time online** (optional): download models once using `scripts/download_models.py`, then run fully offline afterwards.

---

### RAG (Retrieval Augmented Generation) – K1 only

RAG is enabled **only** for the **K1 (LLM conversation)** mode.

- **Vector DB**: ChromaDB (persistent on disk)
- **Embeddings**: `sentence-transformers` with `all-MiniLM-L6-v2` (CPU)
- **Knowledge base source**: all `.txt` files in `data/knowledge_base/` loaded at startup
- **Chunking**: 500 characters per chunk with 100 character overlap
- **Retrieval**: top 3 chunks by cosine similarity
- **Prompt format**:
  - SYSTEM: “Use the provided context to answer clearly. If context is insufficient, answer normally.”
  - CONTEXT: retrieved chunks
  - USER: user question
- **Memory**: every (question, answer) pair is added back into ChromaDB and capped to the **last 100** conversations

If the vector DB is empty or retrieval fails, the assistant **automatically falls back** to a normal (non‑RAG) LLM prompt.

---

### Project structure

- **`main.py`**: boot, threads, event loop
- **`controller.py`**: routes button events to features
- **`hardware/`**
  - **`buttons.py`**: GPIO polling, emits events (K1/K2/K3)
  - **`oled.py`**: text + streaming token display
  - **`animation.py`**: robot eye animation thread
- **`audio/`**
  - **`recorder.py`**: push‑to‑talk recording via `sounddevice`
  - **`stt.py`**: offline STT using Vosk (`models/vosk/`)
  - **`tts.py`**: offline TTS via `espeak`
- **`ai/`**
  - **`llm.py`**: llama.cpp binding (`llama-cpp-python`), streams tokens to OLED/TTS
  - **`vision.py`**: PiCamera2 capture + YOLOv8 detection (`models/yolo.pt`)
- **`rag/`**
  - **`embedder.py`**: singleton embedding model (loaded once)
  - **`vector_store.py`**: persistent ChromaDB wrapper (`rag/chroma_db/`)
  - **`retriever.py`**: KB indexing + retrieval + conversation memory
- **`data/knowledge_base/`**: your offline `.txt` notes for RAG
- **`storage/images/`**: saved captures
- **`scripts/download_models.py`**: downloads Gemma GGUF, YOLO, and Vosk models

---

### Installation (Raspberry Pi OS recommended)

From the `assistant/` folder:

```bash
sudo apt update
sudo apt install -y \
  python3-pip python3-venv \
  espeak \
  portaudio19-dev \
  libatlas-base-dev

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install rpi-lgpio
```

Enable **Camera** and **I²C** in `raspi-config`, then reboot.

---

### Models (one‑time download)

From `assistant/`:

```bash
source venv/bin/activate
python scripts/download_models.py
```

This downloads:

- **LLM (GGUF)** → `models/gemma-3-4b-it-IQ4_XS.gguf`
- **YOLOv8n** → `models/yolo.pt`
- **Vosk STT** → extracted into `models/vosk/`

You can swap models by replacing these files/dirs.

---

### Running

```bash
cd assistant
source venv/bin/activate
python main.py
```

On boot, the OLED shows the idle **robot eyes** animation.

---

### Controls

- **K2 (GPIO27) – Object detection**
  - Captures a still image
  - Runs YOLOv8 (CPU)
  - Shows the first detected label on OLED and speaks it

- **K3 short (< 1s) – Image capture**
  - Captures an image
  - Saves it under `storage/images/capture_YYYYMMDD_HHMMSS.jpg`

- **K1 long (≥ 1s) – LLM conversation (push‑to‑talk)**
  - OLED: “Listening…” while recording
  - STT: Vosk transcribes audio
  - RAG (K1 only): retrieves top 3 chunks from ChromaDB
  - LLM: llama.cpp streams response token‑by‑token to OLED
  - TTS: speaks the final answer
  - Memory: stores this Q&A back into ChromaDB (keeps last 100)

---

### Troubleshooting

- **`GPIO unavailable ... Cannot determine SOC peripheral base address`**
  - If you’re running on a non‑Pi machine, this is expected (buttons are disabled).
  - On a Raspberry Pi, ensure you’re using Raspberry Pi OS and try running with:

    ```bash
    sudo venv/bin/python main.py
    ```

- **`Bus error` followed by `Input/output error` from `ls` / `cd`**
  - This typically indicates **SD card / storage corruption or failure**, not a Python bug.
  - Back up what you can, run `fsck`, and migrate to a healthy SD card.

- **ChromaDB / RAG schema errors after upgrades**
  - Stop the assistant and delete the local vector DB to rebuild:

    ```bash
    rm -rf rag/chroma_db
    ```

---

### Notes

- This project is designed to run **fully offline** once the models are present.
- RAG affects **only** K1 chat mode; K2 (object detection) and K3 (image capture) remain unchanged.

