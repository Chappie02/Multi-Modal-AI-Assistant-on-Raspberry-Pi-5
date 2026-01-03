"""
LLM Engine Module
Local LLM inference using llama.cpp with token streaming.

This module provides:
- llama.cpp integration for local LLM inference
- Token-by-token streaming for real-time display
- Context management and prompt formatting
- Support for Gemma-3-4B-IT model
"""

from typing import Iterator, Optional, Callable, List
import os
import subprocess
import json
import tempfile

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("llama-cpp-python not available. Install with: pip install llama-cpp-python")


class LLMEngine:
    """
    Local LLM inference engine using llama.cpp.
    
    Supports token streaming for real-time display updates.
    Uses Gemma-3-4B-IT model in GGUF format.
    """
    
    def __init__(self,
                 model_path: str = "models/gemma-2-2b-it-q4_k_m.gguf",
                 n_ctx: int = 2048,
                 n_threads: int = 4,
                 temperature: float = 0.7,
                 top_p: float = 0.9):
        """
        Initialize LLM engine.
        
        Args:
            model_path: Path to GGUF model file
            n_ctx: Context window size
            n_threads: Number of CPU threads for inference
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
        """
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.temperature = temperature
        self.top_p = top_p
        
        self.llm = None
        self._initialized = False
        
    def initialize(self) -> bool:
        """
        Load LLM model.
        This may take several seconds and requires significant RAM.
        
        Returns:
            True if initialization successful
        """
        if not LLAMA_CPP_AVAILABLE:
            print("llama-cpp-python not available")
            print("Install with: pip install llama-cpp-python")
            return False
        
        if not os.path.exists(self.model_path):
            print(f"Model file not found: {self.model_path}")
            print("Please download Gemma-3-4B-IT GGUF model from HuggingFace")
            return False
        
        try:
            print(f"Loading LLM model: {self.model_path}")
            print("This may take 30-60 seconds...")
            
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                verbose=False
            )
            
            self._initialized = True
            print("LLM model loaded successfully")
            return True
            
        except Exception as e:
            print(f"LLM initialization failed: {e}")
            return False
    
    def generate(self,
                 prompt: str,
                 max_tokens: int = 256,
                 stream: bool = True,
                 token_callback: Optional[Callable[[str], None]] = None) -> Iterator[str]:
        """
        Generate text from prompt with token streaming.
        
        Args:
            prompt: Input prompt text
            max_tokens: Maximum tokens to generate
            stream: If True, yield tokens as they're generated
            token_callback: Optional callback function for each token
        
        Yields:
            Generated tokens (words or subwords) as strings
        """
        if not self._initialized:
            if not self.initialize():
                yield "Error: LLM not initialized"
                return
        
        try:
            # Format prompt for instruction-tuned model
            formatted_prompt = self._format_prompt(prompt)
            
            # Generate with streaming
            stream_obj = self.llm(
                formatted_prompt,
                max_tokens=max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                stream=stream,
                stop=["</s>", "\n\n\n"]  # Stop sequences
            )
            
            if stream:
                # Yield tokens as they arrive
                full_text = ""
                for output in stream_obj:
                    token = output['choices'][0]['text']
                    full_text += token
                    
                    # Call callback if provided
                    if token_callback:
                        token_callback(token)
                    
                    yield token
            else:
                # Return complete text
                result = stream_obj['choices'][0]['text']
                yield result
                
        except Exception as e:
            print(f"LLM generation failed: {e}")
            yield f"Error: {str(e)}"
    
    def generate_complete(self, prompt: str, max_tokens: int = 256) -> str:
        """
        Generate complete response (non-streaming).
        
        Args:
            prompt: Input prompt text
            max_tokens: Maximum tokens to generate
        
        Returns:
            Complete generated text
        """
        result = ""
        for token in self.generate(prompt, max_tokens, stream=False):
            result += token
        return result
    
    def _format_prompt(self, prompt: str) -> str:
        """
        Format prompt for instruction-tuned model (Gemma-IT).
        
        Args:
            prompt: User prompt
        
        Returns:
            Formatted prompt with instruction template
        """
        # Gemma-3-4B-IT uses a specific format
        # Adjust based on actual model requirements
        formatted = f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
        return formatted
    
    def format_with_context(self, user_input: str, context: List[str]) -> str:
        """
        Format prompt with RAG context.
        
        Args:
            user_input: Current user input
            context: List of relevant context strings from RAG
        
        Returns:
            Formatted prompt with context
        """
        if not context:
            return user_input
        
        # Build context section
        context_text = "\n\nRelevant context from previous conversations:\n"
        for i, ctx in enumerate(context, 1):
            context_text += f"{i}. {ctx}\n"
        
        # Combine with user input
        full_prompt = f"{context_text}\n\nUser: {user_input}\nAssistant:"
        return full_prompt
    
    def is_available(self) -> bool:
        """Check if LLM is initialized and ready."""
        return self._initialized
    
    def cleanup(self):
        """Clean up model resources."""
        self.llm = None
        self._initialized = False

