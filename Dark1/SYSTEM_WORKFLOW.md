# System Workflow - Step-by-Step Explanation

This document explains the complete system workflow for both Chat Mode and Object Detection Mode, detailing how each component interacts.

## 🔄 Chat Mode Workflow

### Step 1: Idle State
- **LCD**: Displays robot eyes animation (blinking effect)
- **Wake Word Detector**: Continuously listening for "Hey Pi"
- **System**: Low CPU usage, waiting for activation

### Step 2: Wake Word Detection
```
User says "Hey Pi"
    ↓
Wake Word Detector (Porcupine or simple keyword matching)
    ↓
Callback triggered → _on_wake_word_detected()
    ↓
Acquire processing lock (prevents concurrent requests)
```

### Step 3: Listening State
- **LCD**: Switches to "Listening..." state
  - Pulsing green circle animation
  - "Listening..." text displayed
- **STT**: Starts recording audio (5 seconds default)
- **Microphone**: Captures audio stream at 16kHz

### Step 4: Speech-to-Text
```
Audio recording complete
    ↓
STT Engine (Vosk or Whisper)
    ↓
Audio → Text conversion
    ↓
User input: "What is the capital of France?"
```

### Step 5: Mode Check
- **Mode Manager**: Checks if command is mode switch
  - "Switch to chat mode" → Change mode
  - "Switch to object detection mode" → Change mode
- If not mode switch, proceed to processing

### Step 6: Thinking State
- **LCD**: Switches to "Thinking..." state
  - Rotating spinner animation
  - "Thinking..." text
- **RAG Memory**: Retrieves relevant context
  ```
  Query: "What is the capital of France?"
    ↓
  Semantic search in conversation history
    ↓
  Top-K (default 3) relevant past conversations
    ↓
  Context: ["Q: What is France? A: France is a country...", ...]
  ```

### Step 7: LLM Prompt Formatting
- **LLM Engine**: Formats prompt with context
  ```
  Relevant context from previous conversations:
  1. Q: What is France? A: France is a country...
  
  User: What is the capital of France?
  Assistant:
  ```

### Step 8: Token Streaming
- **LCD**: Switches to "Speaking" state
- **LLM Engine**: Generates response token-by-token
  ```
  llama.cpp inference
    ↓
  Token 1: "The"
    ↓
  Token callback → UI append_token("The")
    ↓
  LCD updates immediately
    ↓
  Token 2: " capital"
    ↓
  Token callback → UI append_token(" capital")
    ↓
  LCD updates (text grows)
    ↓
  ... continues until complete
  ```
- **UI Renderer**: 
  - Maintains text buffer
  - Wraps text to fit LCD width
  - Scrolls if text exceeds height
  - Updates display after each token

### Step 9: Text-to-Speech
- **TTS Engine**: Converts complete response to speech
  ```
  Full response: "The capital of France is Paris."
    ↓
  TTS (Piper/espeak)
    ↓
  Audio synthesis
    ↓
  Playback through speaker
  ```

### Step 10: Memory Storage
- **RAG Memory**: Stores conversation
  ```
  Conversation:
    - User: "What is the capital of France?"
    - Assistant: "The capital of France is Paris."
    - Mode: "chat"
    - Timestamp: 2024-01-15T10:30:00
    - Embedding: [0.123, -0.456, ...] (384-dim vector)
    ↓
  SQLite INSERT
    ↓
  Stored for future retrieval
  ```

### Step 11: Return to Idle
- **LCD**: Returns to idle state (robot eyes)
- **Processing Lock**: Released
- **System**: Ready for next wake word

---

## 🔍 Object Detection Mode Workflow

### Step 1: Trigger Phrase Detection
```
User says "what is this?" (or "detect objects")
    ↓
Mode Manager detects trigger phrase
    ↓
If in Chat Mode → Switch to Object Detection Mode
```

### Step 2: Detection State
- **LCD**: Switches to "Detecting..." state
  - Camera icon displayed
  - "Detecting..." text

### Step 3: Image Capture
- **Camera Module**: Captures single frame
  ```
  Picamera2 initialization
    ↓
  Capture frame (640×480 RGB)
    ↓
  Frame: numpy array (480, 640, 3)
  ```

### Step 4: Object Detection
- **YOLO Detector**: Runs inference
  ```
  Frame preprocessing
    ↓
  Resize to 640×640 (YOLO input size)
    ↓
  Normalize to [0, 1]
    ↓
  YOLOv8n inference
    ↓
  Post-processing:
    - Non-maximum suppression (NMS)
    - Confidence filtering (threshold: 0.25)
    ↓
  Detections: [
    ("person", 0.95, (x1, y1, x2, y2)),
    ("laptop", 0.87, (x1, y1, x2, y2)),
    ("book", 0.72, (x1, y1, x2, y2))
  ]
  ```

### Step 5: Display Detections
- **UI Renderer**: Shows detection results
  ```
  LCD displays:
    "Detected Objects"
    "person (95%)"
    "laptop (87%)"
    "book (72%)"
  ```

### Step 6: LLM Explanation
- **Detector**: Formats for LLM
  ```
  Detection text: "Detected: a person (confidence: 95%), 
                   a laptop (confidence: 87%), 
                   a book (confidence: 72%)."
  ```
- **LLM Engine**: Generates natural explanation
  ```
  Prompt: "Explain these detected objects in a natural, 
          conversational way: Detected: a person..."
    ↓
  Token streaming (same as Chat Mode)
    ↓
  Response: "I can see a person sitting at a desk with 
            a laptop and a book. The person appears to be 
            working or studying."
  ```

### Step 7: Display and Speak
- **LCD**: Shows explanation token-by-token
- **TTS**: Speaks explanation

### Step 8: Memory Storage
- **RAG Memory**: Stores object detection
  ```
  Object Detection:
    - Labels: ["person", "laptop", "book"]
    - Description: "I can see a person..."
    - Timestamp: 2024-01-15T10:35:00
    - Embedding: [0.789, -0.234, ...]
    ↓
  SQLite INSERT into objects table
  ```

### Step 9: Return to Idle
- **LCD**: Returns to idle state
- **System**: Ready for next command

---

## 🔀 Mode Switching Workflow

### Voice-Based Switching
```
User: "Switch to chat mode"
    ↓
STT: Transcribes command
    ↓
Mode Manager: handle_voice_command()
    ↓
Detects mode switch phrase
    ↓
set_mode(SystemMode.CHAT)
    ↓
Mode change callback triggered
    ↓
LCD: "Mode: Chat Mode"
    ↓
System ready in new mode
```

### Hardware Switch (Optional)
```
GPIO button pressed
    ↓
Hardware interrupt triggered
    ↓
_hw_switch_callback()
    ↓
Toggle between CHAT and OBJECT_DETECTION
    ↓
Mode change callback
    ↓
LCD updates
```

---

## 🧠 RAG Memory Retrieval Details

### Semantic Search Process

1. **Query Embedding**
   ```
   User query: "What is the capital of France?"
     ↓
   Sentence Transformer (all-MiniLM-L6-v2)
     ↓
   Embedding vector: [0.123, -0.456, 0.789, ...] (384 dimensions)
   ```

2. **Database Query**
   ```
   SELECT user_input, assistant_output, embedding
   FROM conversations
   WHERE mode = 'chat'
   ```

3. **Similarity Calculation**
   ```
   For each stored conversation:
     - Load embedding from database
     - Calculate cosine similarity:
       similarity = dot(query_embedding, stored_embedding) / 
                    (norm(query) * norm(stored))
     - Store (similarity, conversation_text)
   ```

4. **Top-K Selection**
   ```
   Sort by similarity (descending)
     ↓
   Select top 3 conversations
     ↓
   Return context strings
   ```

5. **Context Injection**
   ```
   Context appended to LLM prompt:
   
   Relevant context from previous conversations:
   1. Q: What is France? A: France is a country...
   2. Q: Tell me about Europe. A: Europe is...
   3. Q: What languages are spoken in France? A: French...
   
   User: What is the capital of France?
   Assistant:
   ```

---

## 📊 Data Flow Diagram

```
┌─────────────┐
│   User      │
│  (Voice)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│ Wake Word   │────▶│    STT      │
│  Detector   │     │  (Vosk)     │
└─────────────┘     └──────┬───────┘
                           │
                           ▼
                    ┌─────────────┐
                    │Mode Manager │
                    └──────┬──────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                      │
        ▼                                      ▼
┌──────────────┐                    ┌──────────────────┐
│  Chat Mode   │                    │ Object Detection  │
└──────┬───────┘                    │      Mode         │
       │                            └─────────┬──────────┘
       │                                      │
       ▼                                      ▼
┌─────────────┐                    ┌─────────────┐
│ RAG Memory  │                    │   Camera    │
│ (Retrieve)  │                    └──────┬──────┘
└──────┬──────┘                           │
       │                                   ▼
       ▼                            ┌─────────────┐
┌─────────────┐                     │   YOLO      │
│ LLM Engine  │                     │  Detector   │
│ (Generate)  │                     └──────┬──────┘
└──────┬──────┘                            │
       │                                    │
       ├─────────── Token Stream ───────────┤
       │                                    │
       ▼                                    ▼
┌─────────────┐                    ┌─────────────┐
│ UI Renderer │                    │ UI Renderer │
│  (Display)  │                    │  (Display)  │
└──────┬──────┘                    └──────┬──────┘
       │                                   │
       └───────────────┬───────────────────┘
                       │
                       ▼
              ┌─────────────┐
              │     TTS     │
              │  (Piper)    │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │   Speaker    │
              └─────────────┘
                     │
                     ▼
              ┌─────────────┐
              │ RAG Memory   │
              │  (Store)     │
              └─────────────┘
```

---

## ⚡ Performance Characteristics

### Latency Breakdown (Chat Mode)

- **Wake Word Detection**: < 100ms
- **Audio Recording**: 5000ms (5 seconds)
- **STT Processing**: 500-2000ms (Vosk) or 2000-5000ms (Whisper)
- **RAG Retrieval**: 50-200ms
- **LLM First Token**: 500-2000ms (depends on model size)
- **LLM Generation**: 50-200ms per token
- **TTS Synthesis**: 100-500ms per sentence
- **Total**: ~8-15 seconds for complete interaction

### Latency Breakdown (Object Detection)

- **Image Capture**: 100-300ms
- **YOLO Inference**: 200-800ms (YOLOv8n on Pi 5)
- **LLM Explanation**: 1000-3000ms
- **TTS**: 1000-2000ms
- **Total**: ~2-6 seconds

### Resource Usage

- **RAM**: 2-3GB (with 2B model)
- **CPU**: 50-80% during inference
- **Storage**: ~5GB (models + database)

---

## 🔒 Error Handling

### Camera Failure
```
Camera.capture_frame() returns None
    ↓
UI: "Camera error"
    ↓
Return to idle (graceful degradation)
```

### LLM Timeout
```
LLM generation exceeds timeout
    ↓
Fallback: "I'm having trouble processing that"
    ↓
Log error, continue operation
```

### LCD Communication Error
```
SPI transfer fails
    ↓
Retry with backoff (3 attempts)
    ↓
If still fails: Continue without display updates
```

### Audio Device Missing
```
TTS/STT initialization fails
    ↓
Warn user: "Audio not available"
    ↓
Continue with text-only interaction
```

---

This workflow ensures robust, production-grade operation with proper error handling and graceful degradation.

