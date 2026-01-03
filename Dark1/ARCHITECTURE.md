# Raspberry Pi 5 Multimodal LLM Assistant - System Architecture

## System Overview

This is a production-grade embedded AI assistant running entirely offline on Raspberry Pi 5. The system integrates voice interaction, computer vision, local LLM inference, and a custom LCD display to create an intelligent multimodal assistant.

## Hardware Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Raspberry Pi 5                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │  Camera  │  │  Audio   │  │   LCD    │  │   GPIO  ││
│  │ (SPI/CSI)│  │ (USB/BT) │  │  (SPI)   │  │  Pins   ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
│       │             │             │            │        │
│       └─────────────┴─────────────┴────────────┘        │
│                        │                                 │
│              ┌─────────▼─────────┐                      │
│              │   Main Controller │                      │
│              │    (main.py)      │                      │
│              └─────────┬─────────┘                      │
└────────────────────────┼────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │  LLM    │    │   RAG   │    │  YOLO   │
    │ Engine  │    │ Memory  │    │ Detector│
    └─────────┘    └─────────┘    └─────────┘
```

## Software Architecture

### Module Hierarchy

```
main.py (Orchestrator)
│
├── core/
│   ├── llm_engine.py      # llama.cpp integration, token streaming
│   ├── rag_memory.py      # Vector store, semantic search
│   └── mode_manager.py    # Chat/Object Detection mode switching
│
├── audio/
│   ├── wake_word.py       # Keyword spotting (e.g., "Hey Pi")
│   ├── stt.py             # Offline speech-to-text (Vosk/Whisper)
│   └── tts.py             # Offline text-to-speech (piper/espeak)
│
├── vision/
│   ├── camera.py          # Picamera2 wrapper
│   └── detector.py        # YOLOv8 object detection
│
└── display/
    ├── lcd_driver.py      # ST7789P SPI driver (raw implementation)
    └── ui_renderer.py     # Token streaming, UI states, animations
```

## System Workflow

### 1. Chat Mode Workflow

```
[Idle State]
    │
    ├─ Wake Word Detected ("Hey Pi")
    │
    ├─ LCD: "Listening..." animation
    │
    ├─ STT: Record audio → Convert to text
    │
    ├─ LCD: "Thinking..." animation
    │
    ├─ RAG: Retrieve relevant context from memory
    │
    ├─ LLM: Generate response (token-by-token)
    │   │
    │   └─ LCD: Stream tokens as they arrive
    │
    ├─ TTS: Convert response to speech
    │
    ├─ RAG: Store conversation in memory
    │
    └─ Return to Idle State
```

### 2. Object Detection Mode Workflow

```
[Idle State]
    │
    ├─ Trigger Phrase Detected ("what is this?")
    │
    ├─ LCD: "Capturing..." animation
    │
    ├─ Camera: Capture single frame
    │
    ├─ YOLO: Detect objects in frame
    │   │
    │   └─ Returns: [("person", 0.95, bbox), ("laptop", 0.87, bbox)]
    │
    ├─ LLM: Generate natural explanation from detections
    │   │
    │   └─ Prompt: "Explain these objects: person, laptop"
    │
    ├─ LCD: Display explanation (token-by-token)
    │
    ├─ TTS: Speak explanation
    │
    ├─ RAG: Store object + location + timestamp
    │
    └─ Return to Idle State
```

### 3. Mode Switching

- Voice command: "Switch to chat mode" / "Switch to object detection mode"
- Hardware switch: Optional GPIO button for mode toggle
- Default: Chat mode on startup

## LCD Display System

### ST7789P Controller Details

- **Interface**: SPI (4-wire)
- **Resolution**: 240 × 284 pixels
- **Color Depth**: RGB565 (16-bit)
- **Frame Buffer**: 240 × 284 × 2 = 136,320 bytes

### SPI Communication Protocol

1. **Initialization Sequence**:
   - Hardware reset (RST pin)
   - Software reset command
   - Display configuration commands
   - Memory access mode setup
   - Display ON

2. **Pixel Data Transfer**:
   - Set column/row addresses
   - Send pixel data in RGB565 format
   - Chunk size: ≤ 4096 bytes (SPI buffer limit)
   - CS pin managed by spidev automatically

3. **Token Streaming**:
   - Maintain text buffer
   - Render text word-by-word as tokens arrive
   - Scroll if text exceeds display height
   - Use PIL for text rendering to bitmap

### Display States

- **IDLE**: Robot eyes animation / status indicator
- **LISTENING**: "Listening..." with pulsing animation
- **THINKING**: "Thinking..." with spinner
- **SPEAKING**: Token-by-token text display
- **DETECTING**: "Detecting objects..." with progress

## RAG Memory System

### Storage Backend

- **Primary**: SQLite (lightweight, embedded)
- **Vector Store**: ChromaDB or FAISS (for semantic search)
- **Schema**:
  ```sql
  conversations (id, timestamp, mode, input, output, embedding)
  objects (id, timestamp, labels, location, description, embedding)
  ```

### Retrieval Strategy

1. **Embedding Generation**: Use LLM embedding model or sentence transformers
2. **Similarity Search**: Cosine similarity on conversation embeddings
3. **Context Injection**: Top-K relevant conversations appended to LLM prompt

## LLM Integration (llama.cpp)

### Model: Gemma-3-4B-IT

- **Format**: GGUF quantized (Q4_K_M or Q5_K_M for balance)
- **Streaming**: Token callback for real-time display
- **Context Window**: 2048 tokens (configurable)
- **Temperature**: 0.7 (balanced creativity)

### Token Streaming Implementation

```python
def stream_tokens(prompt):
    for token in llama.generate(prompt, stream=True):
        yield token
        # Update LCD immediately
        ui_renderer.append_token(token)
```

## Object Detection (YOLO)

### Model Selection

- **YOLOv8n** (nano): Fastest, suitable for Pi 5
- **YOLOv5s**: Alternative, slightly more accurate
- **Input Size**: 640×640 (standard)
- **Post-processing**: NMS threshold 0.5, confidence 0.25

### Detection Pipeline

1. Capture frame (240×284 or upscale to 640×640)
2. Preprocess (normalize, BGR→RGB)
3. Run inference
4. Post-process (NMS, filter low confidence)
5. Format labels for LLM prompt

## Audio Processing

### Wake Word Detection

- **Library**: Porcupine (offline, low latency)
- **Model**: Custom "Hey Pi" wake word
- **Alternative**: Simple keyword matching on STT output

### Speech-to-Text (STT)

- **Primary**: Vosk (offline, lightweight)
- **Alternative**: Whisper.cpp (more accurate, heavier)
- **Language**: English
- **Sample Rate**: 16kHz

### Text-to-Speech (TTS)

- **Primary**: Piper TTS (offline, natural)
- **Alternative**: espeak-ng (faster, robotic)
- **Voice**: en_US-lessac-medium
- **Output**: Audio stream to speaker

## Performance Considerations

### Optimization Strategies

1. **LLM**: Use quantized models (Q4/Q5), limit context window
2. **YOLO**: Use nano variant, reduce input resolution if needed
3. **LCD**: Double buffering, partial updates only
4. **Audio**: Pre-load models, use threading for I/O
5. **RAG**: Batch embedding generation, cache frequent queries

### Resource Management

- **CPU**: Multi-threading for parallel tasks
- **Memory**: Model loading on demand, cleanup after use
- **GPU**: Not available on Pi 5 (CPU-only inference)

## Error Handling

- **Camera failure**: Graceful degradation, notify user
- **LLM timeout**: Fallback to cached responses
- **LCD communication error**: Retry with backoff
- **Audio device missing**: Warn user, continue without audio

## Security & Privacy

- **All processing local**: No cloud services
- **No data transmission**: Complete privacy
- **Secure storage**: Encrypted RAG database (optional)

## Future Enhancements

- Home automation integration (MQTT/Home Assistant)
- Multi-language support
- Custom wake words
- Voice cloning for TTS
- Edge TPU acceleration (if available)

