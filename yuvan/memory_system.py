"""
Advanced Memory System for Yuvan AI Assistant
Provides persistent memory, context retention, and semantic search capabilities
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import chromadb
from sentence_transformers import SentenceTransformer
import pickle
import threading
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class Memory:
    """Represents a single memory entry"""
    id: str
    content: str
    timestamp: datetime
    memory_type: str  # 'conversation', 'task', 'preference', 'fact'
    importance: float  # 0-1 scale
    tags: List[str]
    context: Dict[str, Any]
    access_count: int = 0
    last_accessed: datetime = None

class MemorySystem:
    """Advanced memory system with semantic search and persistence"""
    
    def __init__(self, memory_dir: str = "memory_storage"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB for semantic search
        self.chroma_client = chromadb.PersistentClient(path=str(self.memory_dir / "chroma_db"))
        self.collection = self.chroma_client.get_or_create_collection(
            name="yuvan_memories",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Memory storage
        self.memories: Dict[str, Memory] = {}
        self.conversation_context: List[Dict] = []
        self.user_preferences: Dict[str, Any] = {}
        self.task_history: List[Dict] = []
        
        # Load existing memories
        self._load_memories()
        
        # Background cleanup thread
        self._start_cleanup_thread()
    
    def add_memory(self, content: str, memory_type: str = "conversation", 
                   importance: float = 0.5, tags: List[str] = None, 
                   context: Dict[str, Any] = None) -> str:
        """Add a new memory entry"""
        memory_id = f"{memory_type}_{int(time.time())}_{hash(content) % 10000}"
        
        memory = Memory(
            id=memory_id,
            content=content,
            timestamp=datetime.now(),
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            context=context or {},
            last_accessed=datetime.now()
        )
        
        self.memories[memory_id] = memory
        
        # Add to ChromaDB for semantic search
        embedding = self.embedding_model.encode([content])[0].tolist()
        self.collection.add(
            embeddings=[embedding],
            documents=[content],
            metadatas=[{
                "memory_id": memory_id,
                "memory_type": memory_type,
                "importance": importance,
                "timestamp": memory.timestamp.isoformat(),
                "tags": ",".join(tags or [])
            }],
            ids=[memory_id]
        )
        
        # Save to disk
        self._save_memory(memory)
        
        return memory_id
    
    def search_memories(self, query: str, limit: int = 10, 
                       memory_type: Optional[str] = None,
                       min_importance: float = 0.0) -> List[Memory]:
        """Search memories using semantic similarity"""
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # Build where clause for filtering
        where_clause = {"importance": {"$gte": min_importance}}
        if memory_type:
            where_clause["memory_type"] = memory_type
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_clause
        )
        
        memories = []
        if results['ids'] and results['ids'][0]:
            for memory_id in results['ids'][0]:
                if memory_id in self.memories:
                    memory = self.memories[memory_id]
                    memory.access_count += 1
                    memory.last_accessed = datetime.now()
                    memories.append(memory)
        
        return memories
    
    def get_recent_context(self, hours: int = 24, limit: int = 20) -> List[Memory]:
        """Get recent conversation context"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_memories = [
            memory for memory in self.memories.values()
            if memory.timestamp > cutoff_time and memory.memory_type == "conversation"
        ]
        
        # Sort by timestamp and importance
        recent_memories.sort(key=lambda m: (m.timestamp, m.importance), reverse=True)
        
        return recent_memories[:limit]
    
    def update_user_preference(self, key: str, value: Any):
        """Update user preferences"""
        self.user_preferences[key] = value
        self._save_preferences()
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference"""
        return self.user_preferences.get(key, default)
    
    def add_task_memory(self, task: str, result: str, success: bool = True,
                       context: Dict[str, Any] = None):
        """Add task execution memory"""
        task_memory = {
            "task": task,
            "result": result,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        self.task_history.append(task_memory)
        
        # Also add as searchable memory
        content = f"Task: {task}\nResult: {result}\nSuccess: {success}"
        self.add_memory(
            content=content,
            memory_type="task",
            importance=0.8 if success else 0.6,
            tags=["task", "execution"],
            context=task_memory
        )
        
        self._save_task_history()
    
    def get_similar_tasks(self, task: str, limit: int = 5) -> List[Memory]:
        """Find similar tasks from history"""
        return self.search_memories(
            query=task,
            limit=limit,
            memory_type="task"
        )
    
    def consolidate_memories(self):
        """Consolidate and compress old memories"""
        cutoff_time = datetime.now() - timedelta(days=30)
        
        old_memories = [
            memory for memory in self.memories.values()
            if memory.timestamp < cutoff_time and memory.access_count < 2
        ]
        
        # Remove low-importance, rarely accessed memories
        for memory in old_memories:
            if memory.importance < 0.3:
                self._remove_memory(memory.id)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        total_memories = len(self.memories)
        memory_types = {}
        
        for memory in self.memories.values():
            memory_types[memory.memory_type] = memory_types.get(memory.memory_type, 0) + 1
        
        return {
            "total_memories": total_memories,
            "memory_types": memory_types,
            "user_preferences": len(self.user_preferences),
            "task_history": len(self.task_history),
            "storage_size": self._get_storage_size()
        }
    
    def _load_memories(self):
        """Load memories from disk"""
        memories_file = self.memory_dir / "memories.json"
        preferences_file = self.memory_dir / "preferences.json"
        tasks_file = self.memory_dir / "tasks.json"
        
        # Load memories
        if memories_file.exists():
            try:
                with open(memories_file, 'r') as f:
                    memories_data = json.load(f)
                    for memory_id, memory_dict in memories_data.items():
                        memory_dict['timestamp'] = datetime.fromisoformat(memory_dict['timestamp'])
                        if memory_dict.get('last_accessed'):
                            memory_dict['last_accessed'] = datetime.fromisoformat(memory_dict['last_accessed'])
                        self.memories[memory_id] = Memory(**memory_dict)
            except Exception as e:
                print(f"Error loading memories: {e}")
        
        # Load preferences
        if preferences_file.exists():
            try:
                with open(preferences_file, 'r') as f:
                    self.user_preferences = json.load(f)
            except Exception as e:
                print(f"Error loading preferences: {e}")
        
        # Load task history
        if tasks_file.exists():
            try:
                with open(tasks_file, 'r') as f:
                    self.task_history = json.load(f)
            except Exception as e:
                print(f"Error loading task history: {e}")
    
    def _save_memory(self, memory: Memory):
        """Save a single memory to disk"""
        self._save_all_memories()
    
    def _save_all_memories(self):
        """Save all memories to disk"""
        memories_file = self.memory_dir / "memories.json"
        
        # Convert memories to serializable format
        memories_data = {}
        for memory_id, memory in self.memories.items():
            memory_dict = asdict(memory)
            memory_dict['timestamp'] = memory.timestamp.isoformat()
            if memory.last_accessed:
                memory_dict['last_accessed'] = memory.last_accessed.isoformat()
            memories_data[memory_id] = memory_dict
        
        with open(memories_file, 'w') as f:
            json.dump(memories_data, f, indent=2)
    
    def _save_preferences(self):
        """Save user preferences to disk"""
        preferences_file = self.memory_dir / "preferences.json"
        with open(preferences_file, 'w') as f:
            json.dump(self.user_preferences, f, indent=2)
    
    def _save_task_history(self):
        """Save task history to disk"""
        tasks_file = self.memory_dir / "tasks.json"
        with open(tasks_file, 'w') as f:
            json.dump(self.task_history, f, indent=2)
    
    def _remove_memory(self, memory_id: str):
        """Remove a memory from storage"""
        if memory_id in self.memories:
            del self.memories[memory_id]
            
            # Remove from ChromaDB
            try:
                self.collection.delete(ids=[memory_id])
            except Exception:
                pass
            
            self._save_all_memories()
    
    def _get_storage_size(self) -> str:
        """Get total storage size"""
        total_size = 0
        for file_path in self.memory_dir.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        # Convert to human readable format
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total_size < 1024.0:
                return f"{total_size:.2f} {unit}"
            total_size /= 1024.0
        return f"{total_size:.2f} TB"
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                time.sleep(3600)  # Run every hour
                try:
                    self.consolidate_memories()
                except Exception as e:
                    print(f"Memory cleanup error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self._save_all_memories()
            self._save_preferences()
            self._save_task_history()
        except Exception:
            pass