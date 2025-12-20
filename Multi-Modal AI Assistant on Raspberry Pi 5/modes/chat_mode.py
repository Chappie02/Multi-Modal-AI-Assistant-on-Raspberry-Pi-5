"""
Chat Mode Implementation
Handles text-based conversation using local LLM via llama.cpp.
"""

import os
from typing import Optional
from llama_cpp import Llama


class ChatMode:
    """Handles chat mode functionality using local LLM."""
    
    def __init__(self):
        """Initialize chat mode with LLM."""
        self.llm: Optional[Llama] = None
        self.system_prompt = """You are a helpful AI assistant running locally on a Raspberry Pi 5. 
You are designed to be helpful, harmless, and honest. You can assist with various tasks 
including answering questions, providing explanations, and helping with general inquiries. 
Keep your responses concise but informative."""
        
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the local LLM using llama.cpp."""
        try:
            # Look for model file in common locations
            model_paths = [
                "./models/llama-7b-q4_0.gguf",
                "./models/llama-7b.gguf", 
                "/home/pi/models/llama-7b-q4_0.gguf",
                "/home/pi/models/llama-7b.gguf",
                "llama-7b-q4_0.gguf"
            ]
            
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if not model_path:
                raise FileNotFoundError(
                    "LLM model file not found. Please download a GGUF model file and place it in the models directory."
                )
            
            print(f"Loading LLM model from: {model_path}")
            
            # Initialize LLM with optimized settings for Raspberry Pi 5
            self.llm = Llama(
                model_path=model_path,
                n_ctx=2048,  # Context window
                n_threads=4,  # Number of threads
                n_gpu_layers=0,  # CPU only for Pi 5
                verbose=False
            )
            
            print("✅ LLM initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing LLM: {e}")
            raise
    
    def generate_response(self, user_message: str) -> str:
        """Generate a response to the user's message."""
        if not self.llm:
            return "❌ LLM not initialized. Please restart the application."
        
        try:
            # Create the conversation prompt
            prompt = f"System: {self.system_prompt}\n\nHuman: {user_message}\n\nAssistant:"
            
            # Generate response
            response = self.llm(
                prompt,
                max_tokens=256,
                temperature=0.7,
                top_p=0.9,
                stop=["Human:", "System:"],
                echo=False
            )
            
            # Extract the generated text
            if response and 'choices' in response and len(response['choices']) > 0:
                generated_text = response['choices'][0]['text'].strip()
                return generated_text
            else:
                return "❌ Failed to generate response. Please try again."
                
        except Exception as e:
            return f"❌ Error generating response: {e}"
    
    def run(self):
        """Run the chat mode loop."""
        if not self.llm:
            print("❌ Chat mode not available. LLM not initialized.")
            return
        
        conversation_count = 0
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() == "exit":
                    print("Exiting chat mode...")
                    break
                
                if not user_input:
                    continue
                
                conversation_count += 1
                print(f"\nAssistant: ", end="", flush=True)
                
                # Generate and display response
                response = self.generate_response(user_input)
                print(response)
                
                # Add a small delay to prevent overwhelming the system
                import time
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n\nExiting chat mode...")
                break
            except Exception as e:
                print(f"\n❌ Error in chat mode: {e}")
                print("Please try again or type 'exit' to return to main menu.")
        
        print(f"Chat session ended. Total conversations: {conversation_count}")
