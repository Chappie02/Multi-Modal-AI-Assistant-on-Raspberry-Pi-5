#!/usr/bin/env python3
"""
Test script for Raspberry Pi 5 Offline AI Assistant
This script tests all components to ensure proper installation.
"""

import sys
import os
import importlib
from pathlib import Path


def test_import(module_name, package_name=None):
    """Test if a module can be imported."""
    try:
        if package_name:
            importlib.import_module(module_name, package_name)
        else:
            importlib.import_module(module_name)
        print(f"✅ {module_name} imported successfully")
        return True
    except ImportError as e:
        print(f"❌ {module_name} import failed: {e}")
        return False


def test_camera():
    """Test camera functionality."""
    print("\n📷 Testing camera...")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                print("✅ Camera test passed")
                return True
        print("❌ Camera test failed - camera not accessible")
        return False
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False


def test_yolo():
    """Test YOLOv8 functionality."""
    print("\n🔍 Testing YOLOv8...")
    try:
        from ultralytics import YOLO
        # This will download the model if not present
        model = YOLO('yolov8n.pt')
        print("✅ YOLOv8 test passed")
        return True
    except Exception as e:
        print(f"❌ YOLOv8 test failed: {e}")
        return False


def test_llama():
    """Test llama.cpp functionality."""
    print("\n🤖 Testing llama.cpp...")
    try:
        from llama_cpp import Llama
        print("✅ llama.cpp import successful")
        
        # Check for model files
        model_paths = [
            'models/llama-7b-q4_0.gguf',
            'models/llama-7b.gguf',
            'models/llama-2-7b-chat.Q4_0.gguf'
        ]
        
        model_found = False
        for path in model_paths:
            if Path(path).exists():
                print(f"✅ LLaMA model found: {path}")
                model_found = True
                break
        
        if not model_found:
            print("⚠️  No LLaMA model found - please download one")
            return False
        
        return True
    except Exception as e:
        print(f"❌ llama.cpp test failed: {e}")
        return False


def test_rag():
    """Test RAG functionality."""
    print("\n📚 Testing RAG components...")
    try:
        from sentence_transformers import SentenceTransformer
        from chromadb import ClientAPI
        print("✅ RAG components imported successfully")
        return True
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        return False


def test_system_utils():
    """Test system utilities."""
    print("\n⚙️ Testing system utilities...")
    try:
        import psutil
        print(f"✅ System info: {psutil.cpu_count()} cores, {psutil.virtual_memory().total / (1024**3):.1f}GB RAM")
        return True
    except Exception as e:
        print(f"❌ System utilities test failed: {e}")
        return False


def test_project_structure():
    """Test project structure."""
    print("\n📁 Testing project structure...")
    
    required_files = [
        'main.py',
        'requirements.txt',
        'README.md',
        'modes/chat_mode.py',
        'modes/object_mode.py',
        'utils/camera_utils.py',
        'utils/llm_utils.py',
        'utils/rag_utils.py',
        'utils/system_utils.py'
    ]
    
    required_dirs = [
        'modes',
        'utils',
        'models'
    ]
    
    all_good = True
    
    # Check directories
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")
            all_good = False
    
    # Check files
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ File exists: {file_path}")
        else:
            print(f"❌ File missing: {file_path}")
            all_good = False
    
    return all_good


def main():
    """Main test function."""
    print("🧪 Raspberry Pi 5 Offline AI Assistant - Installation Test")
    print("=" * 60)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Python Dependencies", lambda: all([
            test_import('cv2'),
            test_import('numpy'),
            test_import('PIL', 'Pillow'),
            test_import('psutil')
        ])),
        ("YOLOv8", test_yolo),
        ("llama.cpp", test_llama),
        ("RAG Components", test_rag),
        ("System Utilities", test_system_utils),
        ("Camera", test_camera)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print("=" * 60)
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The installation is complete.")
        print("You can now run: python main.py")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the installation.")
        print("Refer to the README.md for troubleshooting steps.")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
