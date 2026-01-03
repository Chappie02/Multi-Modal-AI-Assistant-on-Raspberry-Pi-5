"""
RAG Memory System
Retrieval Augmented Generation memory for conversation and object storage.

This module provides:
- SQLite database for conversation storage
- Vector embeddings for semantic search
- Context retrieval for LLM prompts
- Object detection history storage
"""

import sqlite3
import json
from typing import List, Tuple, Optional, Dict
from datetime import datetime
import hashlib

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("sentence-transformers not available. Install with: pip install sentence-transformers")

import numpy as np


class RAGMemory:
    """
    RAG memory system for storing and retrieving conversations and objects.
    
    Uses SQLite for storage and sentence transformers for embeddings.
    Supports semantic search to find relevant context for LLM prompts.
    """
    
    def __init__(self, db_path: str = "rag_memory.db", embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG memory system.
        
        Args:
            db_path: Path to SQLite database file
            embedding_model: Sentence transformer model name
                           (all-MiniLM-L6-v2 is lightweight and fast)
        """
        self.db_path = db_path
        self.embedding_model_name = embedding_model
        self.embedding_model = None
        self.embedding_dim = 384  # Default for all-MiniLM-L6-v2
        
        # Initialize database
        self._init_database()
        
        # Load embedding model
        if EMBEDDINGS_AVAILABLE:
            self._load_embedding_model()
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                mode TEXT NOT NULL,
                user_input TEXT NOT NULL,
                assistant_output TEXT NOT NULL,
                embedding BLOB,
                metadata TEXT
            )
        ''')
        
        # Objects table (for object detection history)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                labels TEXT NOT NULL,
                description TEXT,
                embedding BLOB,
                metadata TEXT
            )
        ''')
        
        # Create index for faster searches
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_embedding_model(self):
        """Load sentence transformer model for embeddings."""
        if not EMBEDDINGS_AVAILABLE:
            return
        
        try:
            print(f"Loading embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            # Get actual embedding dimension
            test_embedding = self.embedding_model.encode("test")
            self.embedding_dim = len(test_embedding)
            print(f"Embedding model loaded (dimension: {self.embedding_dim})")
        except Exception as e:
            print(f"Failed to load embedding model: {e}")
            self.embedding_model = None
    
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector as numpy array, or None if model unavailable
        """
        if not self.embedding_model:
            return None
        
        try:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            print(f"Embedding generation failed: {e}")
            return None
    
    def store_conversation(self, 
                          user_input: str,
                          assistant_output: str,
                          mode: str = "chat") -> int:
        """
        Store a conversation exchange in memory.
        
        Args:
            user_input: User's input text
            assistant_output: Assistant's response
            mode: Conversation mode ("chat" or "object_detection")
        
        Returns:
            ID of stored conversation
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        # Create combined text for embedding
        combined_text = f"{user_input} {assistant_output}"
        embedding = self._get_embedding(combined_text)
        
        # Store embedding as binary
        embedding_blob = None
        if embedding is not None:
            embedding_blob = embedding.tobytes()
        
        # Store metadata as JSON
        metadata = json.dumps({
            "user_length": len(user_input),
            "assistant_length": len(assistant_output)
        })
        
        cursor.execute('''
            INSERT INTO conversations 
            (timestamp, mode, user_input, assistant_output, embedding, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, mode, user_input, assistant_output, embedding_blob, metadata))
        
        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return conversation_id
    
    def store_object_detection(self,
                               labels: List[str],
                               description: str,
                               metadata: Optional[Dict] = None) -> int:
        """
        Store object detection result.
        
        Args:
            labels: List of detected object labels
            description: LLM-generated description
            metadata: Optional metadata (e.g., location, confidence)
        
        Returns:
            ID of stored object detection
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        labels_str = json.dumps(labels)
        metadata_str = json.dumps(metadata) if metadata else None
        
        # Create text for embedding
        detection_text = f"{', '.join(labels)}. {description}"
        embedding = self._get_embedding(detection_text)
        
        embedding_blob = None
        if embedding is not None:
            embedding_blob = embedding.tobytes()
        
        cursor.execute('''
            INSERT INTO objects 
            (timestamp, labels, description, embedding, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, labels_str, description, embedding_blob, metadata_str))
        
        object_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return object_id
    
    def retrieve_context(self,
                        query: str,
                        top_k: int = 3,
                        mode: Optional[str] = None) -> List[str]:
        """
        Retrieve relevant context for a query using semantic search.
        
        Args:
            query: Query text to find relevant context for
            top_k: Number of top results to return
            mode: Filter by mode ("chat" or "object_detection"), None for all
        
        Returns:
            List of relevant context strings
        """
        if not self.embedding_model:
            # Fallback to simple text-based retrieval
            return self._retrieve_simple(query, top_k, mode)
        
        # Generate query embedding
        query_embedding = self._get_embedding(query)
        if query_embedding is None:
            return self._retrieve_simple(query, top_k, mode)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query
        if mode:
            cursor.execute('''
                SELECT user_input, assistant_output, embedding
                FROM conversations
                WHERE mode = ?
            ''', (mode,))
        else:
            cursor.execute('''
                SELECT user_input, assistant_output, embedding
                FROM conversations
            ''')
        
        results = cursor.fetchall()
        conn.close()
        
        # Calculate similarities
        similarities = []
        for user_input, assistant_output, embedding_blob in results:
            if embedding_blob is None:
                continue
            
            # Load stored embedding
            stored_embedding = np.frombuffer(embedding_blob, dtype=np.float32)
            
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, stored_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
            )
            
            similarities.append((similarity, f"Q: {user_input}\nA: {assistant_output}"))
        
        # Sort by similarity and return top K
        similarities.sort(reverse=True, key=lambda x: x[0])
        context = [text for _, text in similarities[:top_k]]
        
        return context
    
    def _retrieve_simple(self, query: str, top_k: int, mode: Optional[str]) -> List[str]:
        """
        Simple text-based retrieval (fallback when embeddings unavailable).
        
        Args:
            query: Query text
            top_k: Number of results
            mode: Filter by mode
        
        Returns:
            List of context strings
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        if mode:
            cursor.execute('''
                SELECT user_input, assistant_output, timestamp
                FROM conversations
                WHERE mode = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (mode, top_k * 3))  # Get more to filter
        else:
            cursor.execute('''
                SELECT user_input, assistant_output, timestamp
                FROM conversations
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (top_k * 3,))
        
        results = cursor.fetchall()
        conn.close()
        
        # Simple keyword matching
        scored = []
        for user_input, assistant_output, timestamp in results:
            text = f"{user_input} {assistant_output}".lower()
            text_words = set(text.split())
            
            # Count matching words
            matches = len(query_words & text_words)
            if matches > 0:
                scored.append((matches, f"Q: {user_input}\nA: {assistant_output}"))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return [text for _, text in scored[:top_k]]
    
    def get_recent_conversations(self, limit: int = 5) -> List[Tuple[str, str]]:
        """
        Get recent conversations (for debugging/display).
        
        Args:
            limit: Number of recent conversations to return
        
        Returns:
            List of (user_input, assistant_output) tuples
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_input, assistant_output
            FROM conversations
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def cleanup(self):
        """Clean up resources."""
        # Database connection is closed after each operation
        # Embedding model stays loaded for performance
        pass

