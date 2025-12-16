"""
Memory management system for chat conversations and long-term context.
Provides short-term conversation memory and long-term session memory.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import pickle


class Message(BaseModel):
    """Individual message in conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create from dictionary."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class ConversationMemory:
    """
    Short-term conversation memory.
    Maintains recent conversation context with sliding window.
    """
    
    def __init__(self, max_messages: int = 10, max_tokens: int = 4000):
        """
        Initialize conversation memory.
        
        Args:
            max_messages: Maximum number of messages to keep
            max_tokens: Approximate max tokens (rough estimate: 4 chars = 1 token)
        """
        self.messages: List[Message] = []
        self.max_messages = max_messages
        self.max_tokens = max_tokens
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to conversation history."""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self._trim_messages()
    
    def add_user_message(self, content: str, metadata: Dict[str, Any] = None):
        """Add user message."""
        self.add_message("user", content, metadata)
    
    def add_assistant_message(self, content: str, metadata: Dict[str, Any] = None):
        """Add assistant message."""
        self.add_message("assistant", content, metadata)
    
    def _trim_messages(self):
        """Trim messages to stay within limits."""
        # Keep only recent messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        
        # Estimate tokens and trim if needed
        total_chars = sum(len(msg.content) for msg in self.messages)
        estimated_tokens = total_chars // 4  # Rough estimate
        
        while estimated_tokens > self.max_tokens and len(self.messages) > 2:
            # Keep at least 2 messages (latest user + assistant)
            self.messages.pop(0)
            total_chars = sum(len(msg.content) for msg in self.messages)
            estimated_tokens = total_chars // 4
    
    def get_messages(self, n: Optional[int] = None) -> List[Message]:
        """
        Get recent messages.
        
        Args:
            n: Number of recent messages to get (None = all)
        
        Returns:
            List of messages
        """
        if n is None:
            return self.messages.copy()
        return self.messages[-n:]
    
    def get_formatted_history(self, n: Optional[int] = None) -> str:
        """
        Get conversation history formatted as string for LLM context.
        
        Args:
            n: Number of recent messages (None = all)
        
        Returns:
            Formatted conversation string
        """
        messages = self.get_messages(n)
        if not messages:
            return "No previous conversation."
        
        formatted = []
        for msg in messages:
            formatted.append(f"{msg.role.upper()}: {msg.content}")
        
        return "\n\n".join(formatted)
    
    def get_langchain_format(self, n: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get messages in LangChain format.
        
        Args:
            n: Number of recent messages
        
        Returns:
            List of dicts with 'role' and 'content'
        """
        messages = self.get_messages(n)
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    def clear(self):
        """Clear all messages."""
        self.messages = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "messages": [msg.to_dict() for msg in self.messages],
            "max_messages": self.max_messages,
            "max_tokens": self.max_tokens
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMemory":
        """Create from dictionary."""
        memory = cls(
            max_messages=data.get("max_messages", 10),
            max_tokens=data.get("max_tokens", 4000)
        )
        memory.messages = [Message.from_dict(msg) for msg in data.get("messages", [])]
        return memory


class SessionMemory:
    """
    Long-term session memory.
    Stores conversation summaries, user preferences, and insights.
    """
    
    def __init__(self, session_id: str, storage_dir: str = "data/sessions"):
        """
        Initialize session memory.
        
        Args:
            session_id: Unique session identifier
            storage_dir: Directory to store session files
        """
        self.session_id = session_id
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Session data
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.conversation_summaries: List[str] = []
        self.user_preferences: Dict[str, Any] = {}
        self.query_history: List[Dict[str, Any]] = []
        self.insights: List[str] = []
        self.metadata: Dict[str, Any] = {}
        
        # Load existing session if available
        self._load()
    
    @property
    def session_file(self) -> Path:
        """Get session file path."""
        return self.storage_dir / f"{self.session_id}.json"
    
    def add_query_record(self, query: str, result_summary: str, success: bool = True):
        """
        Record a query and its result.
        
        Args:
            query: User query
            result_summary: Summary of result
            success: Whether query was successful
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "result_summary": result_summary,
            "success": success
        }
        self.query_history.append(record)
        self.last_accessed = datetime.now()
        
        # Keep only recent queries (last 100)
        if len(self.query_history) > 100:
            self.query_history = self.query_history[-100:]
    
    def add_conversation_summary(self, summary: str):
        """Add a conversation summary."""
        self.conversation_summaries.append({
            "timestamp": datetime.now().isoformat(),
            "summary": summary
        })
        
        # Keep only recent summaries (last 20)
        if len(self.conversation_summaries) > 20:
            self.conversation_summaries = self.conversation_summaries[-20:]
    
    def set_preference(self, key: str, value: Any):
        """Set user preference."""
        self.user_preferences[key] = value
        self.last_accessed = datetime.now()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference."""
        return self.user_preferences.get(key, default)
    
    def add_insight(self, insight: str):
        """Add an insight about user or usage patterns."""
        self.insights.append({
            "timestamp": datetime.now().isoformat(),
            "insight": insight
        })
        
        # Keep only recent insights (last 50)
        if len(self.insights) > 50:
            self.insights = self.insights[-50:]
    
    def get_context_summary(self) -> str:
        """
        Get a summary of session context for LLM.
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # User preferences
        if self.user_preferences:
            prefs = ", ".join([f"{k}: {v}" for k, v in self.user_preferences.items()])
            context_parts.append(f"User Preferences: {prefs}")
        
        # Recent query patterns
        if self.query_history:
            recent_queries = [q["query"] for q in self.query_history[-5:]]
            context_parts.append(f"Recent queries: {'; '.join(recent_queries)}")
        
        # Insights
        if self.insights:
            recent_insights = [i["insight"] for i in self.insights[-3:]]
            context_parts.append(f"Insights: {'; '.join(recent_insights)}")
        
        if not context_parts:
            return "No session context available."
        
        return "\n".join(context_parts)
    
    def save(self):
        """Save session to disk."""
        data = {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "conversation_summaries": self.conversation_summaries,
            "user_preferences": self.user_preferences,
            "query_history": self.query_history,
            "insights": self.insights,
            "metadata": self.metadata
        }
        
        with open(self.session_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        """Load session from disk if exists."""
        if not self.session_file.exists():
            return
        
        try:
            with open(self.session_file, "r") as f:
                data = json.load(f)
            
            self.created_at = datetime.fromisoformat(data["created_at"])
            self.last_accessed = datetime.fromisoformat(data["last_accessed"])
            self.conversation_summaries = data.get("conversation_summaries", [])
            self.user_preferences = data.get("user_preferences", {})
            self.query_history = data.get("query_history", [])
            self.insights = data.get("insights", [])
            self.metadata = data.get("metadata", {})
        except Exception as e:
            print(f"Warning: Could not load session {self.session_id}: {e}")
    
    def delete(self):
        """Delete session file."""
        if self.session_file.exists():
            self.session_file.unlink()
    
    @classmethod
    def list_sessions(cls, storage_dir: str = "data/sessions") -> List[str]:
        """List all session IDs."""
        storage_path = Path(storage_dir)
        if not storage_path.exists():
            return []
        
        return [f.stem for f in storage_path.glob("*.json")]


class MemoryManager:
    """
    Combined memory manager handling both short-term and long-term memory.
    """
    
    def __init__(
        self,
        session_id: str,
        max_conversation_messages: int = 10,
        max_conversation_tokens: int = 4000,
        storage_dir: str = "data/sessions"
    ):
        """
        Initialize memory manager.
        
        Args:
            session_id: Unique session identifier
            max_conversation_messages: Max messages in short-term memory
            max_conversation_tokens: Max tokens in short-term memory
            storage_dir: Directory for long-term storage
        """
        self.conversation_memory = ConversationMemory(
            max_messages=max_conversation_messages,
            max_tokens=max_conversation_tokens
        )
        self.session_memory = SessionMemory(session_id, storage_dir)
    
    def add_exchange(
        self,
        user_message: str,
        assistant_message: str,
        result_summary: Optional[str] = None,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a complete user-assistant exchange.
        
        Args:
            user_message: User's message
            assistant_message: Assistant's response
            result_summary: Summary for long-term storage
            success: Whether the exchange was successful
            metadata: Additional metadata
        """
        # Add to short-term memory
        self.conversation_memory.add_user_message(user_message, metadata)
        self.conversation_memory.add_assistant_message(assistant_message, metadata)
        
        # Record in long-term memory
        summary = result_summary or assistant_message[:200]
        self.session_memory.add_query_record(user_message, summary, success)
    
    def get_context_for_llm(self) -> str:
        """
        Get complete context for LLM including both short and long-term memory.
        
        Returns:
            Formatted context string
        """
        parts = []
        
        # Session context
        session_context = self.session_memory.get_context_summary()
        if session_context != "No session context available.":
            parts.append("## Session Context\n" + session_context)
        
        # Recent conversation
        conversation = self.conversation_memory.get_formatted_history()
        if conversation != "No previous conversation.":
            parts.append("## Recent Conversation\n" + conversation)
        
        if not parts:
            return "No context available."
        
        return "\n\n".join(parts)
    
    def save_session(self):
        """Save long-term session memory."""
        self.session_memory.save()
    
    def clear_conversation(self):
        """Clear short-term conversation memory."""
        self.conversation_memory.clear()
    
    def export_session(self) -> Dict[str, Any]:
        """
        Export complete session data.
        
        Returns:
            Dictionary with all session data
        """
        return {
            "session_id": self.session_memory.session_id,
            "conversation": self.conversation_memory.to_dict(),
            "session": {
                "created_at": self.session_memory.created_at.isoformat(),
                "last_accessed": self.session_memory.last_accessed.isoformat(),
                "preferences": self.session_memory.user_preferences,
                "query_count": len(self.session_memory.query_history),
                "insights": self.session_memory.insights
            }
        }
