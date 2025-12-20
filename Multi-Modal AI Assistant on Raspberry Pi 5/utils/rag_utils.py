"""
RAG (Retrieval-Augmented Generation) Utilities
Optional RAG implementation using sentence transformers and ChromaDB.
"""

import os
import json
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer


class RAGManager:
    """Manages RAG operations for enhanced context retrieval."""
    
    def __init__(self, collection_name: str = "ai_assistant_kb"):
        """
        Initialize RAG manager.
        
        Args:
            collection_name: Name of the ChromaDB collection
        """
        self.collection_name = collection_name
        self.embedding_model: Optional[SentenceTransformer] = None
        self.chroma_client: Optional[chromadb.ClientAPI] = None
        self.collection: Optional[chromadb.Collection] = None
        
        self._initialize_rag()
    
    def _initialize_rag(self):
        """Initialize RAG components."""
        try:
            # Initialize embedding model
            print("Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize ChromaDB
            print("Initializing ChromaDB...")
            self.chroma_client = chromadb.PersistentClient(
                path="./chroma_db"
            )
            
            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(
                    name=self.collection_name
                )
                print(f"✅ Loaded existing collection: {self.collection_name}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name
                )
                print(f"✅ Created new collection: {self.collection_name}")
                
                # Add some default knowledge
                self._add_default_knowledge()
            
            print("✅ RAG system initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing RAG: {e}")
            print("RAG functionality will be disabled.")
            self.embedding_model = None
            self.chroma_client = None
            self.collection = None
    
    def _add_default_knowledge(self):
        """Add default knowledge base entries."""
        default_knowledge = [
            {
                "content": "The Raspberry Pi 5 is a single-board computer with 4GB or 8GB RAM options, featuring a quad-core ARM Cortex-A76 processor.",
                "metadata": {"source": "hardware", "topic": "raspberry_pi"}
            },
            {
                "content": "YOLOv8 is a state-of-the-art object detection model that can identify and locate objects in images with high accuracy.",
                "metadata": {"source": "ai", "topic": "object_detection"}
            },
            {
                "content": "llama.cpp is a C++ implementation for running LLaMA models locally on CPU with optimized performance.",
                "metadata": {"source": "ai", "topic": "llm"}
            },
            {
                "content": "OpenCV is a computer vision library that provides tools for image processing, camera access, and computer vision tasks.",
                "metadata": {"source": "library", "topic": "computer_vision"}
            }
        ]
        
        self.add_documents(default_knowledge)
    
    def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a single document to the knowledge base.
        
        Args:
            content: Document content
            metadata: Optional metadata
        """
        if not self.collection:
            return False
        
        try:
            # Generate embedding
            embedding = self.embedding_model.encode(content).tolist()
            
            # Add to collection
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata or {}],
                ids=[f"doc_{len(self.collection.get()['ids'])}"]
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding document: {e}")
            return False
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add multiple documents to the knowledge base.
        
        Args:
            documents: List of documents with 'content' and optional 'metadata'
        """
        if not self.collection:
            return False
        
        try:
            contents = [doc['content'] for doc in documents]
            metadatas = [doc.get('metadata', {}) for doc in documents]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(contents).tolist()
            
            # Generate IDs
            ids = [f"doc_{i}" for i in range(len(contents))]
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ Added {len(documents)} documents to knowledge base")
            return True
            
        except Exception as e:
            print(f"❌ Error adding documents: {e}")
            return False
    
    def search(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant documents.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of relevant documents
        """
        if not self.collection:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                        'distance': results['distances'][0][i] if results['distances'] and results['distances'][0] else 0
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error searching knowledge base: {e}")
            return []
    
    def get_context_for_query(self, query: str, max_context_length: int = 500) -> str:
        """
        Get relevant context for a query to enhance LLM responses.
        
        Args:
            query: User query
            max_context_length: Maximum length of context to return
            
        Returns:
            Formatted context string
        """
        results = self.search(query, n_results=3)
        
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for result in results:
            content = result['content']
            if current_length + len(content) <= max_context_length:
                context_parts.append(content)
                current_length += len(content)
            else:
                break
        
        if context_parts:
            return "Relevant context:\n" + "\n".join(context_parts) + "\n\n"
        
        return ""
    
    def is_available(self) -> bool:
        """Check if RAG functionality is available."""
        return self.collection is not None and self.embedding_model is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics."""
        if not self.collection:
            return {"available": False}
        
        try:
            collection_data = self.collection.get()
            return {
                "available": True,
                "document_count": len(collection_data['ids']) if collection_data['ids'] else 0,
                "collection_name": self.collection_name
            }
        except:
            return {"available": False}


def initialize_rag_system() -> Optional[RAGManager]:
    """
    Initialize RAG system with error handling.
    
    Returns:
        RAGManager instance if successful, None otherwise
    """
    try:
        return RAGManager()
    except Exception as e:
        print(f"⚠️  RAG system initialization failed: {e}")
        print("Continuing without RAG functionality...")
        return None
