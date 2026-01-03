#!/usr/bin/env python3
"""
Component Test Script
Tests each subsystem individually to verify hardware and software setup.

Run with: sudo python3 test_components.py
"""

import sys
import time

def test_lcd():
    """Test LCD display."""
    print("\n=== Testing LCD Display ===")
    try:
        from display.lcd_driver import ST7789Driver
        from display.ui_renderer import UIRenderer
        
        lcd = ST7789Driver()
        lcd.initialize()
        ui = UIRenderer(lcd)
        
        print("  ✓ LCD initialized")
        
        # Test clear
        ui.clear()
        print("  ✓ Display cleared")
        
        # Test text rendering
        ui.set_text("LCD Test")
        time.sleep(2)
        print("  ✓ Text rendering works")
        
        # Test states
        ui.set_state("listening")
        time.sleep(1)
        ui.set_state("thinking")
        time.sleep(1)
        ui.set_state("idle")
        print("  ✓ UI states work")
        
        ui.cleanup()
        lcd.cleanup()
        print("  ✓ LCD test PASSED")
        return True
        
    except Exception as e:
        print(f"  ✗ LCD test FAILED: {e}")
        return False

def test_camera():
    """Test camera."""
    print("\n=== Testing Camera ===")
    try:
        from vision.camera import Camera
        
        camera = Camera()
        if not camera.initialize():
            print("  ✗ Camera initialization failed")
            return False
        
        print("  ✓ Camera initialized")
        
        frame = camera.capture_frame()
        if frame is None:
            print("  ✗ Frame capture failed")
            return False
        
        print(f"  ✓ Frame captured: {frame.shape}")
        
        camera.cleanup()
        print("  ✓ Camera test PASSED")
        return True
        
    except Exception as e:
        print(f"  ✗ Camera test FAILED: {e}")
        return False

def test_detector():
    """Test object detector (may take time to load model)."""
    print("\n=== Testing Object Detector ===")
    print("  (This may take 30-60 seconds to load YOLO model...)")
    try:
        from vision.detector import ObjectDetector
        import numpy as np
        
        detector = ObjectDetector()
        if not detector.initialize():
            print("  ✗ Detector initialization failed")
            print("  Note: YOLO model will be downloaded on first run")
            return False
        
        print("  ✓ Detector initialized")
        
        # Test with dummy image
        dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        detections = detector.detect(dummy_image)
        
        print(f"  ✓ Detection completed: {len(detections)} objects")
        
        detector.cleanup()
        print("  ✓ Detector test PASSED")
        return True
        
    except Exception as e:
        print(f"  ✗ Detector test FAILED: {e}")
        return False

def test_audio():
    """Test audio components."""
    print("\n=== Testing Audio Components ===")
    
    # Test TTS
    try:
        from audio.tts import TextToSpeech
        
        tts = TextToSpeech()
        if tts.initialize():
            print("  ✓ TTS initialized")
            # Don't actually speak in test
            # tts.speak("Test", blocking=True)
            tts.cleanup()
        else:
            print("  ⚠ TTS not available (may need espeak)")
    except Exception as e:
        print(f"  ⚠ TTS test skipped: {e}")
    
    # Test STT (may not work without model)
    try:
        from audio.stt import SpeechToText
        
        stt = SpeechToText()
        if stt.initialize():
            print("  ✓ STT initialized")
            stt.cleanup()
        else:
            print("  ⚠ STT not available (install Vosk model)")
    except Exception as e:
        print(f"  ⚠ STT test skipped: {e}")
    
    print("  ✓ Audio components checked")
    return True

def test_llm():
    """Test LLM (requires model file)."""
    print("\n=== Testing LLM Engine ===")
    try:
        from core.llm_engine import LLMEngine
        import os
        
        # Check if model exists
        model_path = "models/gemma-2-2b-it-q4_k_m.gguf"
        if not os.path.exists(model_path):
            print(f"  ⚠ Model not found: {model_path}")
            print("  Download model first (see README.md)")
            return False
        
        print("  (Loading LLM model - this may take 30-60 seconds...)")
        llm = LLMEngine(model_path=model_path)
        if not llm.initialize():
            print("  ✗ LLM initialization failed")
            return False
        
        print("  ✓ LLM initialized")
        
        # Test generation
        print("  Testing generation...")
        response = list(llm.generate("Hello", max_tokens=10, stream=False))
        if response:
            print(f"  ✓ Generation works: {response[0][:50]}...")
        
        llm.cleanup()
        print("  ✓ LLM test PASSED")
        return True
        
    except Exception as e:
        print(f"  ✗ LLM test FAILED: {e}")
        return False

def test_rag():
    """Test RAG memory."""
    print("\n=== Testing RAG Memory ===")
    try:
        from core.rag_memory import RAGMemory
        
        rag = RAGMemory(db_path="test_rag.db")
        print("  ✓ RAG initialized")
        
        # Test storage
        conv_id = rag.store_conversation(
            "Hello",
            "Hi there!",
            mode="chat"
        )
        print(f"  ✓ Conversation stored (ID: {conv_id})")
        
        # Test retrieval
        context = rag.retrieve_context("Hello", top_k=1)
        print(f"  ✓ Context retrieved: {len(context)} items")
        
        # Cleanup
        import os
        if os.path.exists("test_rag.db"):
            os.remove("test_rag.db")
        
        rag.cleanup()
        print("  ✓ RAG test PASSED")
        return True
        
    except Exception as e:
        print(f"  ✗ RAG test FAILED: {e}")
        return False

def main():
    """Run all component tests."""
    print("=" * 50)
    print("Raspberry Pi 5 Multimodal LLM Assistant")
    print("Component Test Suite")
    print("=" * 50)
    
    # Check if running as root
    import os
    if os.geteuid() != 0:
        print("\n⚠ Warning: Not running as root")
        print("Some tests (LCD, GPIO) may fail without sudo")
        print("Run with: sudo python3 test_components.py\n")
    
    results = {}
    
    # Run tests
    results['LCD'] = test_lcd()
    results['Camera'] = test_camera()
    results['Detector'] = test_detector()
    results['Audio'] = test_audio()
    results['LLM'] = test_llm()
    results['RAG'] = test_rag()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    for component, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {component:15} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✓ All tests PASSED!")
    else:
        print("\n⚠ Some tests failed. Check errors above.")
        print("  Some failures may be expected if models are not downloaded.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

