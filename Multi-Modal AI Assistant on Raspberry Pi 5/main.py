#!/usr/bin/env python3
"""
Raspberry Pi 5 Offline AI Assistant
Main entry point for the CLI-based AI assistant.

This application provides two modes:
1. Chat Mode: Text-based conversation using local LLM
2. Object Detection Mode: Camera-based object detection with scene summarization
"""

import sys
import os
from typing import Optional

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modes.chat_mode import ChatMode
from modes.object_mode import ObjectMode
from utils.system_utils import print_banner, check_system_requirements


class AIAssistant:
    """Main controller for the AI Assistant application."""
    
    def __init__(self):
        self.chat_mode: Optional[ChatMode] = None
        self.object_mode: Optional[ObjectMode] = None
        self.current_mode = None
    
    def print_main_menu(self):
        """Print the main menu options."""
        print("\n" + "="*60)
        print("🤖 Raspberry Pi 5 Offline AI Assistant")
        print("="*60)
        print("Available modes:")
        print("1. 'chat mode' - Text-based conversation with local LLM")
        print("2. 'object mode' - Camera-based object detection and analysis")
        print("3. 'exit' - Exit the application")
        print("="*60)
    
    def initialize_modes(self):
        """Initialize chat and object detection modes."""
        try:
            print("Initializing AI models...")
            self.chat_mode = ChatMode()
            self.object_mode = ObjectMode()
            print("✅ AI models initialized successfully!")
        except Exception as e:
            print(f"❌ Error initializing AI models: {e}")
            print("Please check your model files and dependencies.")
            return False
        return True
    
    def run_chat_mode(self):
        """Run chat mode."""
        if not self.chat_mode:
            print("❌ Chat mode not initialized. Please restart the application.")
            return
        
        print("\n💬 Chat Mode Activated")
        print("Type your messages and press Enter. Type 'exit' to return to main menu.")
        print("-" * 50)
        
        self.current_mode = "chat"
        self.chat_mode.run()
        self.current_mode = None
    
    def run_object_mode(self):
        """Run object detection mode."""
        if not self.object_mode:
            print("❌ Object mode not initialized. Please restart the application.")
            return
        
        print("\n📷 Object Detection Mode Activated")
        print("Type 'what is this' to analyze the scene, or 'exit' to return to main menu.")
        print("-" * 50)
        
        self.current_mode = "object"
        self.object_mode.run()
        self.current_mode = None
    
    def run(self):
        """Main application loop."""
        print_banner()
        
        # Check system requirements
        if not check_system_requirements():
            print("❌ System requirements not met. Please check your setup.")
            return
        
        # Initialize AI modes
        if not self.initialize_modes():
            return
        
        # Main application loop
        while True:
            try:
                self.print_main_menu()
                user_input = input("\nEnter your choice: ").strip().lower()
                
                if user_input == "exit":
                    print("\n👋 Thank you for using the AI Assistant!")
                    break
                elif user_input == "chat mode":
                    self.run_chat_mode()
                elif user_input == "object mode":
                    self.run_object_mode()
                else:
                    print("❌ Invalid choice. Please enter 'chat mode', 'object mode', or 'exit'.")
            
            except KeyboardInterrupt:
                print("\n\n👋 Application interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                print("Please try again or restart the application.")


def main():
    """Main entry point."""
    try:
        assistant = AIAssistant()
        assistant.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
