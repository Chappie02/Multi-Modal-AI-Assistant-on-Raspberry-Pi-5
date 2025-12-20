"""
System Utilities
Handles system monitoring, requirements checking, and utility functions.
"""

import os
import sys
import psutil
import platform
from typing import Dict, Any, List


def print_banner():
    """Print the application banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        🤖 Raspberry Pi 5 Offline AI Assistant 🤖            ║
    ║                                                              ║
    ║    Powered by: llama.cpp + YOLOv8 + OpenCV + ChromaDB       ║
    ║                                                              ║
    ║    Features:                                                 ║
    ║    • Local LLM Chat Mode                                     ║
    ║    • Camera-based Object Detection                           ║
    ║    • Scene Analysis and Summarization                        ║
    ║    • Fully Offline Operation                                 ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_system_requirements() -> bool:
    """
    Check if the system meets the requirements for running the AI assistant.
    
    Returns:
        True if requirements are met, False otherwise
    """
    print("🔍 Checking system requirements...")
    
    requirements_met = True
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8+ required")
        requirements_met = False
    else:
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check available memory
    memory = psutil.virtual_memory()
    memory_gb = memory.total / (1024**3)
    if memory_gb < 3:
        print(f"❌ Insufficient RAM: {memory_gb:.1f}GB (4GB+ recommended)")
        requirements_met = False
    else:
        print(f"✅ Available RAM: {memory_gb:.1f}GB")
    
    # Check CPU cores
    cpu_count = psutil.cpu_count()
    if cpu_count < 4:
        print(f"⚠️  Limited CPU cores: {cpu_count} (4+ recommended)")
    else:
        print(f"✅ CPU cores: {cpu_count}")
    
    # Check available disk space
    disk = psutil.disk_usage('/')
    disk_free_gb = disk.free / (1024**3)
    if disk_free_gb < 5:
        print(f"❌ Insufficient disk space: {disk_free_gb:.1f}GB (5GB+ recommended)")
        requirements_met = False
    else:
        print(f"✅ Available disk space: {disk_free_gb:.1f}GB")
    
    # Check for required directories
    required_dirs = ['./models', './chroma_db']
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"✅ Created directory: {dir_path}")
            except:
                print(f"⚠️  Could not create directory: {dir_path}")
    
    return requirements_met


def get_system_info() -> Dict[str, Any]:
    """
    Get comprehensive system information.
    
    Returns:
        Dictionary containing system information
    """
    return {
        'platform': platform.platform(),
        'python_version': sys.version,
        'cpu_count': psutil.cpu_count(),
        'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
        'memory': {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'percent': psutil.virtual_memory().percent
        },
        'disk': {
            'total': psutil.disk_usage('/').total,
            'free': psutil.disk_usage('/').free,
            'percent': psutil.disk_usage('/').percent
        },
        'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
    }


def monitor_system_resources() -> Dict[str, Any]:
    """
    Monitor current system resource usage.
    
    Returns:
        Dictionary containing current resource usage
    """
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'processes': len(psutil.pids())
    }


def check_camera_availability() -> bool:
    """
    Check if camera is available on the system.
    
    Returns:
        True if camera is available, False otherwise
    """
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            return ret and frame is not None
        return False
    except ImportError:
        print("❌ OpenCV not installed")
        return False
    except Exception as e:
        print(f"❌ Camera check failed: {e}")
        return False


def check_model_files() -> Dict[str, bool]:
    """
    Check if required model files are present.
    
    Returns:
        Dictionary indicating which models are available
    """
    model_files = {
        'yolov8n.pt': False,
        'llama_model': False
    }
    
    # Check for YOLOv8 model (will be downloaded automatically)
    model_files['yolov8n.pt'] = True  # ultralytics will handle this
    
    # Check for LLaMA model
    llama_paths = [
        './models/llama-7b-q4_0.gguf',
        './models/llama-7b.gguf',
        '/home/pi/models/llama-7b-q4_0.gguf',
        '/home/pi/models/llama-7b.gguf',
        'llama-7b-q4_0.gguf'
    ]
    
    for path in llama_paths:
        if os.path.exists(path):
            model_files['llama_model'] = True
            break
    
    return model_files


def print_system_status():
    """Print current system status."""
    print("\n📊 System Status:")
    print("-" * 40)
    
    # System resources
    resources = monitor_system_resources()
    print(f"CPU Usage: {resources['cpu_percent']:.1f}%")
    print(f"Memory Usage: {resources['memory_percent']:.1f}%")
    print(f"Disk Usage: {resources['disk_percent']:.1f}%")
    print(f"Active Processes: {resources['processes']}")
    
    # Model availability
    models = check_model_files()
    print(f"\n📁 Model Files:")
    print(f"YOLOv8: {'✅' if models['yolov8n.pt'] else '❌'}")
    print(f"LLaMA Model: {'✅' if models['llama_model'] else '❌'}")
    
    # Camera status
    camera_available = check_camera_availability()
    print(f"Camera: {'✅' if camera_available else '❌'}")


def cleanup_temp_files():
    """Clean up temporary files created during operation."""
    temp_files = [
        './temp_image.jpg',
        './temp_capture.png',
        './debug_output.txt'
    ]
    
    cleaned_count = 0
    for file_path in temp_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                cleaned_count += 1
        except:
            pass
    
    if cleaned_count > 0:
        print(f"🧹 Cleaned up {cleaned_count} temporary files")


def get_recommended_settings() -> Dict[str, Any]:
    """
    Get recommended settings based on system capabilities.
    
    Returns:
        Dictionary with recommended settings
    """
    memory_gb = psutil.virtual_memory().total / (1024**3)
    cpu_count = psutil.cpu_count()
    
    settings = {
        'llm_context_size': 2048 if memory_gb >= 4 else 1024,
        'llm_threads': min(cpu_count, 4),
        'camera_resolution': (640, 480),
        'yolo_confidence_threshold': 0.5,
        'max_conversation_history': 10
    }
    
    # Adjust based on available memory
    if memory_gb < 4:
        settings['llm_context_size'] = 1024
        settings['max_conversation_history'] = 5
    
    return settings
