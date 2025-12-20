"""
LLM Utilities
Handles LLM operations using llama.cpp for local inference.
"""

import os
import psutil
from typing import Optional, Dict, Any
from llama_cpp import Llama


class LLMManager:
    """Manages LLM operations and configurations."""
    
    def __init__(self, model_path: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM manager.
        
        Args:
            model_path: Path to the GGUF model file
            config: Optional configuration dictionary
        """
        self.model_path = model_path
        self.config = config or self._get_default_config()
        self.llm: Optional[Llama] = None
        
        self._initialize_llm()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration optimized for Raspberry Pi 5."""
        return {
            'n_ctx': 2048,           # Context window
            'n_threads': 4,          # Number of CPU threads
            'n_gpu_layers': 0,       # CPU only for Pi 5
            'verbose': False,        # Reduce output verbosity
            'temperature': 0.7,      # Default temperature
            'top_p': 0.9,           # Top-p sampling
            'max_tokens': 256,      # Maximum tokens to generate
        }
    
    def _initialize_llm(self):
        """Initialize the LLM with the given configuration."""
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
            print(f"Loading LLM model from: {self.model_path}")
            
            # Initialize LLM with configuration
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.config['n_ctx'],
                n_threads=self.config['n_threads'],
                n_gpu_layers=self.config['n_gpu_layers'],
                verbose=self.config['verbose']
            )
            
            print("✅ LLM initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing LLM: {e}")
            raise
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the LLM.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        if not self.llm:
            return "❌ LLM not initialized"
        
        try:
            # Merge default config with kwargs
            generation_params = {
                'max_tokens': self.config['max_tokens'],
                'temperature': self.config['temperature'],
                'top_p': self.config['top_p'],
                **kwargs
            }
            
            response = self.llm(prompt, **generation_params)
            
            if response and 'choices' in response and len(response['choices']) > 0:
                return response['choices'][0]['text'].strip()
            else:
                return "❌ Failed to generate response"
                
        except Exception as e:
            return f"❌ Error generating text: {e}"
    
    def chat_completion(self, messages: list, system_prompt: str = "") -> str:
        """
        Generate a chat completion from a list of messages.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt
            
        Returns:
            Generated response
        """
        if not self.llm:
            return "❌ LLM not initialized"
        
        try:
            # Format messages into prompt
            prompt_parts = []
            
            if system_prompt:
                prompt_parts.append(f"System: {system_prompt}")
            
            for message in messages:
                role = message.get('role', 'user')
                content = message.get('content', '')
                prompt_parts.append(f"{role.capitalize()}: {content}")
            
            prompt_parts.append("Assistant:")
            prompt = "\n\n".join(prompt_parts)
            
            return self.generate_text(prompt)
            
        except Exception as e:
            return f"❌ Error in chat completion: {e}"
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for monitoring."""
        return {
            'model_path': self.model_path,
            'config': self.config,
            'memory_usage': psutil.virtual_memory().percent,
            'cpu_usage': psutil.cpu_percent(),
            'is_initialized': self.llm is not None
        }


def find_model_file(model_name: str = "llama-7b-q4_0.gguf") -> Optional[str]:
    """
    Find a model file in common locations.
    
    Args:
        model_name: Name of the model file to find
        
    Returns:
        Path to the model file if found, None otherwise
    """
    search_paths = [
        f"./models/{model_name}",
        f"./{model_name}",
        f"/home/pi/models/{model_name}",
        f"/opt/models/{model_name}",
        f"/usr/local/models/{model_name}",
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            return path
    
    return None


def get_recommended_config_for_pi5() -> Dict[str, Any]:
    """
    Get recommended configuration for Raspberry Pi 5.
    
    Returns:
        Configuration dictionary optimized for Pi 5
    """
    return {
        'n_ctx': 2048,
        'n_threads': 4,
        'n_gpu_layers': 0,
        'verbose': False,
        'temperature': 0.7,
        'top_p': 0.9,
        'max_tokens': 256,
        'repeat_penalty': 1.1,
        'top_k': 40,
    }


def check_model_compatibility(model_path: str) -> bool:
    """
    Check if a model file is compatible with llama.cpp.
    
    Args:
        model_path: Path to the model file
        
    Returns:
        True if compatible, False otherwise
    """
    try:
        if not os.path.exists(model_path):
            return False
        
        # Check file extension
        if not model_path.endswith('.gguf'):
            return False
        
        # Try to load the model briefly
        test_llm = Llama(model_path, n_ctx=512, n_threads=1, verbose=False)
        test_llm = None  # Release memory
        
        return True
        
    except:
        return False
