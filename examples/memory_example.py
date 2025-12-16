#!/usr/bin/env python3
"""
Example: Using Memory Management System
Demonstrates short-term conversation memory and long-term session memory
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.memory import MemoryManager, ConversationMemory, SessionMemory


def demo_conversation_memory():
    """Demonstrate short-term conversation memory."""
    print("="*70)
    print("DEMO 1: Short-Term Conversation Memory")
    print("="*70)
    print()
    
    # Create conversation memory
    memory = ConversationMemory(max_messages=5)
    
    # Simulate a conversation
    exchanges = [
        ("What are the total sales?", "Total sales are $1.2M"),
        ("Show me by month", "Here are monthly sales: Jan: $100K, Feb: $120K..."),
        ("Which month had highest sales?", "February had the highest sales at $120K"),
        ("Create a chart of this", "I've created a bar chart saved to sales_by_month.png"),
        ("What about last year?", "Last year's sales were..."),
    ]
    
    print("Adding conversation messages:\n")
    for i, (user_msg, assistant_msg) in enumerate(exchanges, 1):
        memory.add_user_message(user_msg)
        memory.add_assistant_message(assistant_msg)
        print(f"{i}. USER: {user_msg}")
        print(f"   ASSISTANT: {assistant_msg}\n")
    
    # Show memory
    print("\n" + "-"*70)
    print("Current memory (formatted for LLM):")
    print("-"*70)
    print(memory.get_formatted_history())
    
    # Show that old messages get trimmed
    print("\n" + "-"*70)
    print(f"Total messages in memory: {len(memory.messages)}")
    print(f"Max messages: {memory.max_messages}")
    print("✅ Older messages automatically trimmed!")
    print()


def demo_session_memory():
    """Demonstrate long-term session memory."""
    print("\n" + "="*70)
    print("DEMO 2: Long-Term Session Memory")
    print("="*70)
    print()
    
    # Create session
    session = SessionMemory(session_id="demo_session_001")
    
    # Add user preferences
    print("📝 Setting user preferences...")
    session.set_preference("favorite_chart_type", "bar")
    session.set_preference("default_time_range", "last_30_days")
    session.set_preference("preferred_database", "production")
    print(f"   Preferences: {session.user_preferences}\n")
    
    # Record queries
    print("📊 Recording query history...")
    queries = [
        ("SELECT * FROM sales", "Retrieved 1000 rows", True),
        ("Show me top customers", "Found 10 top customers", True),
        ("invalid sql syntax", "SQL error: syntax invalid", False),
    ]
    
    for query, summary, success in queries:
        session.add_query_record(query, summary, success)
        status = "✅" if success else "❌"
        print(f"   {status} {query}")
    print()
    
    # Add insights
    print("💡 Adding insights...")
    session.add_insight("User frequently asks about sales data")
    session.add_insight("Prefers visual representations")
    print(f"   Insights: {[i['insight'] for i in session.insights]}\n")
    
    # Get context summary
    print("-"*70)
    print("Session Context Summary (for LLM):")
    print("-"*70)
    print(session.get_context_summary())
    print()
    
    # Save session
    print("💾 Saving session to disk...")
    session.save()
    print(f"   Saved to: {session.session_file}")
    print()


def demo_memory_manager():
    """Demonstrate combined memory manager."""
    print("\n" + "="*70)
    print("DEMO 3: Combined Memory Manager")
    print("="*70)
    print()
    
    # Create memory manager
    manager = MemoryManager(
        session_id="demo_session_002",
        max_conversation_messages=6
    )
    
    # Simulate user interactions
    print("💬 Simulating conversation...\n")
    
    exchanges = [
        {
            "user": "What tables are in the database?",
            "assistant": "Found 5 tables: customers, orders, products, sales, inventory",
            "summary": "Listed database tables",
            "success": True
        },
        {
            "user": "Show me customers from New York",
            "assistant": "Found 45 customers from New York",
            "summary": "Filtered customers by location",
            "success": True
        },
        {
            "user": "Create a chart of sales by region",
            "assistant": "Created bar chart showing sales by region. Top region: West Coast with $500K",
            "summary": "Generated sales visualization",
            "success": True
        }
    ]
    
    for i, exchange in enumerate(exchanges, 1):
        print(f"Exchange {i}:")
        print(f"  USER: {exchange['user']}")
        print(f"  ASSISTANT: {exchange['assistant']}\n")
        
        manager.add_exchange(
            user_message=exchange["user"],
            assistant_message=exchange["assistant"],
            result_summary=exchange["summary"],
            success=exchange["success"]
        )
    
    # Set preferences
    manager.session_memory.set_preference("viz_style", "seaborn")
    manager.session_memory.add_insight("User interested in regional analysis")
    
    # Get complete context
    print("-"*70)
    print("Complete Context for LLM:")
    print("-"*70)
    print(manager.get_context_for_llm())
    print()
    
    # Save
    print("💾 Saving session...")
    manager.save_session()
    
    # Export
    print("\n📤 Exporting session data...")
    export = manager.export_session()
    print(f"   Session ID: {export['session_id']}")
    print(f"   Query count: {export['session']['query_count']}")
    print(f"   Created: {export['session']['created_at']}")
    print()


def demo_persistence():
    """Demonstrate memory persistence across sessions."""
    print("\n" + "="*70)
    print("DEMO 4: Memory Persistence")
    print("="*70)
    print()
    
    session_id = "persistent_demo_session"
    
    # First session
    print("📝 Creating new session...")
    session1 = SessionMemory(session_id=session_id)
    session1.set_preference("theme", "dark")
    session1.add_query_record("Initial query", "Initial result", True)
    session1.save()
    print(f"   Preferences: {session1.user_preferences}")
    print(f"   Query count: {len(session1.query_history)}\n")
    
    # Simulate closing and reopening
    print("🔄 Closing and reopening session...\n")
    
    # Second session - should load previous data
    session2 = SessionMemory(session_id=session_id)
    print("✅ Session loaded from disk!")
    print(f"   Preferences: {session2.user_preferences}")
    print(f"   Query count: {len(session2.query_history)}")
    print(f"   Theme: {session2.get_preference('theme')}\n")
    
    # Add more data
    session2.add_query_record("Second session query", "Second result", True)
    session2.save()
    print(f"   Updated query count: {len(session2.query_history)}\n")
    
    # Clean up
    print("🗑️  Cleaning up demo session...")
    session2.delete()
    print("   Demo session deleted")
    print()


def main():
    """Run all demos."""
    print("\n🧠 Memory Management System Demo\n")
    
    # Run demos
    demo_conversation_memory()
    demo_session_memory()
    demo_memory_manager()
    demo_persistence()
    
    # List all sessions
    print("="*70)
    print("All Sessions")
    print("="*70)
    sessions = SessionMemory.list_sessions()
    if sessions:
        print(f"Found {len(sessions)} session(s):")
        for session_id in sessions:
            print(f"  - {session_id}")
    else:
        print("No sessions found")
    
    print("\n" + "="*70)
    print("✅ Demo Complete!")
    print("="*70)
    print("\n💡 Key Features:")
    print("  ✅ Short-term conversation memory (sliding window)")
    print("  ✅ Long-term session memory (persistent)")
    print("  ✅ User preferences tracking")
    print("  ✅ Query history with success tracking")
    print("  ✅ Automatic insights collection")
    print("  ✅ Context generation for LLM")
    print("  ✅ Session persistence across restarts")
    print("\n📁 Session data stored in: data/sessions/")
    print()


if __name__ == "__main__":
    main()
