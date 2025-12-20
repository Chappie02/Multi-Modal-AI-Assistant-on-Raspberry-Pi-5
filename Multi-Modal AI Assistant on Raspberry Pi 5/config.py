"""
Configuration file for Raspberry Pi 5 Offline AI Assistant
Modify these settings based on your system and preferences.
"""

import os
from pathlib import Path

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

# LLaMA model paths (in order of preference)
LLAMA_MODEL_PATHS = [
    "./models/llama-7b-q4_0.gguf",
    "./models/llama-7b.gguf",
    "./models/llama-2-7b-chat.Q4_0.gguf",
    "/home/pi/models/llama-7b-q4_0.gguf",
    "/home/pi/models/llama-7b.gguf"
]

# YOLOv8 model (will be downloaded automatically if not present)
YOLO_MODEL_PATH = "yolov8n.pt"

# =============================================================================
# LLM CONFIGURATION
# =============================================================================

# LLM settings optimized for Raspberry Pi 5
LLM_CONFIG = {
    'n_ctx': 2048,           # Context window size
    'n_threads': 4,          # Number of CPU threads
    'n_gpu_layers': 0,       # GPU layers (0 for CPU only)
    'verbose': False,        # Verbose output
    'temperature': 0.7,      # Response creativity (0.0-1.0)
    'top_p': 0.9,           # Top-p sampling
    'max_tokens': 256,      # Maximum tokens to generate
    'repeat_penalty': 1.1,   # Repetition penalty
    'top_k': 40,            # Top-k sampling
}

# System prompt for the AI assistant
SYSTEM_PROMPT = """You are a helpful AI assistant running locally on a Raspberry Pi 5. 
You are designed to be helpful, harmless, and honest. You can assist with various tasks 
including answering questions, providing explanations, and helping with general inquiries. 
Keep your responses concise but informative."""

# =============================================================================
# CAMERA CONFIGURATION
# =============================================================================

# Camera settings
CAMERA_CONFIG = {
    'index': 0,              # Camera device index
    'resolution': (640, 480), # Camera resolution (width, height)
    'fps': 30,               # Frames per second
    'backend': None,         # OpenCV backend (None for auto-detect)
}

# =============================================================================
# OBJECT DETECTION CONFIGURATION
# =============================================================================

# YOLOv8 settings
YOLO_CONFIG = {
    'confidence_threshold': 0.5,  # Minimum confidence for detections
    'iou_threshold': 0.45,        # IoU threshold for NMS
    'max_detections': 100,        # Maximum number of detections
}

# =============================================================================
# RAG CONFIGURATION
# =============================================================================

# RAG settings
RAG_CONFIG = {
    'collection_name': 'ai_assistant_kb',
    'embedding_model': 'all-MiniLM-L6-v2',
    'chroma_db_path': './chroma_db',
    'max_context_length': 500,
    'n_results': 3,
}

# =============================================================================
# SYSTEM CONFIGURATION
# =============================================================================

# System monitoring settings
SYSTEM_CONFIG = {
    'memory_threshold': 85,       # Memory usage threshold (%)
    'cpu_threshold': 90,          # CPU usage threshold (%)
    'disk_threshold': 90,         # Disk usage threshold (%)
    'monitor_interval': 30,       # Monitoring interval (seconds)
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',              # Logging level
    'file': './ai_assistant.log', # Log file path
    'max_size': 10 * 1024 * 1024, # Max log file size (10MB)
    'backup_count': 5,            # Number of backup log files
}

# =============================================================================
# UI CONFIGURATION
# =============================================================================

# User interface settings
UI_CONFIG = {
    'show_banner': True,          # Show startup banner
    'show_system_info': True,     # Show system information
    'max_conversation_history': 10, # Maximum conversation history
    'auto_save_history': True,    # Auto-save conversation history
}

# =============================================================================
# DEVELOPMENT CONFIGURATION
# =============================================================================

# Development settings
DEBUG = os.getenv('DEBUG', '0') == '1'

# Test mode settings
TEST_MODE = os.getenv('TEST_MODE', '0') == '1'

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_model_path(model_name: str) -> str:
    """Get the full path to a model file."""
    if model_name == 'llama':
        for path in LLAMA_MODEL_PATHS:
            if Path(path).exists():
                return path
        return LLAMA_MODEL_PATHS[0]  # Return first path as fallback
    elif model_name == 'yolo':
        return YOLO_MODEL_PATH
    else:
        return ""

def get_config_for_system() -> dict:
    """Get configuration optimized for the current system."""
    import psutil
    
    # Get system info
    memory_gb = psutil.virtual_memory().total / (1024**3)
    cpu_count = psutil.cpu_count()
    
    # Adjust configuration based on system capabilities
    config = LLM_CONFIG.copy()
    
    if memory_gb < 4:
        config['n_ctx'] = 1024
        config['max_tokens'] = 128
    elif memory_gb >= 8:
        config['n_ctx'] = 4096
        config['max_tokens'] = 512
    
    if cpu_count < 4:
        config['n_threads'] = 2
    elif cpu_count >= 8:
        config['n_threads'] = 6
    
    return config

def validate_config() -> bool:
    """Validate the configuration."""
    errors = []
    
    # Check model paths
    llama_found = False
    for path in LLAMA_MODEL_PATHS:
        if Path(path).exists():
            llama_found = True
            break
    
    if not llama_found:
        errors.append("No LLaMA model found in specified paths")
    
    # Check camera
    try:
        import cv2
        cap = cv2.VideoCapture(CAMERA_CONFIG['index'])
        if not cap.isOpened():
            errors.append("Camera not accessible")
        cap.release()
    except ImportError:
        errors.append("OpenCV not installed")
    
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True

# =============================================================================
# MAIN CONFIGURATION EXPORT
# =============================================================================

# Export main configuration
CONFIG = {
    'llama_model_paths': LLAMA_MODEL_PATHS,
    'yolo_model_path': YOLO_MODEL_PATH,
    'llm_config': LLM_CONFIG,
    'system_prompt': SYSTEM_PROMPT,
    'camera_config': CAMERA_CONFIG,
    'yolo_config': YOLO_CONFIG,
    'rag_config': RAG_CONFIG,
    'system_config': SYSTEM_CONFIG,
    'logging_config': LOGGING_CONFIG,
    'ui_config': UI_CONFIG,
    'debug': DEBUG,
    'test_mode': TEST_MODE,
}

if __name__ == "__main__":
    # Test configuration
    print("🔧 Testing configuration...")
    if validate_config():
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has errors")
        sys.exit(1)
