"""Streamlit app for the multi-agent data analyst chatbot."""

import streamlit as st
from PIL import Image
import os
import sys

# Add parent directory to path for src imports
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.agents.orchestrator import AgentOrchestrator
from src.rag.rag_system import RAGSystem
from src.utils.helpers import format_dataframe_for_display
from src.config import config


# Page configuration
st.set_page_config(
    page_title="Agentic Analytics",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #E3F2FD;
    }
    .assistant-message {
        background-color: #F5F5F5;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = None
    
    if "rag_system" not in st.session_state:
        st.session_state.rag_system = None
    
    if "memory_manager" not in st.session_state:
        # Create unique session ID
        import uuid
        session_id = str(uuid.uuid4())
        from src.utils.memory import MemoryManager
        st.session_state.memory_manager = MemoryManager(
            session_id=session_id,
            max_conversation_messages=10,
            max_conversation_tokens=4000
        )


def initialize_systems():
    """Initialize agent orchestrator and RAG system."""
    try:
        if st.session_state.orchestrator is None:
            with st.spinner("Initializing Agent Orchestrator..."):
                st.session_state.orchestrator = AgentOrchestrator()
        
        if st.session_state.rag_system is None:
            with st.spinner("Initializing RAG System..."):
                st.session_state.rag_system = RAGSystem()
                # Try to load existing index
                try:
                    st.session_state.rag_system.load_index()
                except Exception as load_error:
                    # This is expected on first run - index doesn't exist yet
                    st.info(f"FAISS index not found (this is normal on first run). Click 'Index Database Schema' to create it.")
        
        return True
    except Exception as e:
        import traceback
        st.error(f"Failed to initialize systems: {str(e)}")
        st.error("Please check your .env file and ensure all required API keys are set.")
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
        return False


def display_chat_message(role: str, content: str):
    """Display a chat message.
    
    Args:
        role: 'user' or 'assistant'
        content: Message content
    """
    css_class = "user-message" if role == "user" else "assistant-message"
    icon = "👤" if role == "user" else "🤖"
    
    st.markdown(f"""
    <div class="chat-message {css_class}">
        <strong>{icon} {role.capitalize()}</strong><br/>
        {content}
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application."""
    # Initialize
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🤖 Agentic Analytics</h1>', unsafe_allow_html=True)
    st.markdown("**Multi-Agent Data Analyst Chatbot** powered by LangGraph & RAG")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # System status
        st.subheader("System Status")
        if st.button("Initialize/Reinitialize Systems"):
            st.session_state.orchestrator = None
            st.session_state.rag_system = None
            if initialize_systems():
                st.success("Systems initialized successfully!")
        
        # Display configuration
        st.subheader("Configuration")
        st.text(f"Model: {config.agent_model}")
        st.text(f"Vector Store: {config.vector_store_type}")
        st.text(f"Database: {config.database_url.split('://')[0]}")
        
        st.divider()
        
        # RAG Management
        st.subheader("📚 RAG Management")
        
        if st.button("Index Database Schema"):
            if st.session_state.rag_system:
                try:
                    from src.utils.database import DatabaseManager
                    db = DatabaseManager()
                    schema = db.get_schema_info()
                    st.session_state.rag_system.index_database_schema(schema)
                    st.session_state.rag_system.save_index()
                    st.success("Schema indexed successfully!")
                except Exception as e:
                    import traceback
                    st.error(f"Error: {str(e)}")
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())
        
        # Example queries
        with st.expander("Add Example Queries"):
            example_question = st.text_input("Question")
            example_sql = st.text_area("SQL Query")
            if st.button("Add Example"):
                if example_question and example_sql:
                    st.session_state.rag_system.index_query_examples([{
                        "question": example_question,
                        "sql": example_sql
                    }])
                    st.session_state.rag_system.save_index()
                    st.success("Example added!")
        
        st.divider()
        
        # Clear chat
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                display_chat_message(message["role"], message["content"])
        
        # Chat input
        user_input = st.chat_input("Ask me anything about your data...")
        
        if user_input:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Initialize systems if needed
            if not initialize_systems():
                return
            
            # Process query
            with st.spinner("Processing your query..."):
                try:
                    # Run orchestrator
                    result = st.session_state.orchestrator.run(
                        user_input,
                        st.session_state.messages[:-1]
                    )
                    
                    # Add assistant response
                    response = result.final_answer or "I couldn't process your request."
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Store results for display
                    st.session_state.last_result = result
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
            st.rerun()
    
    with col2:
        st.subheader("📊 Results")
        
        if hasattr(st.session_state, 'last_result') and st.session_state.last_result:
            result = st.session_state.last_result
            
            # Display tabs for different result types
            tabs = st.tabs(["SQL", "Data", "Analysis", "Visualization"])
            
            with tabs[0]:
                if result.sql_query:
                    st.code(result.sql_query, language="sql")
                else:
                    st.info("No SQL query generated")
            
            with tabs[1]:
                if result.query_results is not None:
                    st.dataframe(result.query_results, use_container_width=True)
                else:
                    st.info("No data retrieved")
            
            with tabs[2]:
                if result.analysis_results:
                    st.json(result.analysis_results)
                    if result.analysis_code:
                        with st.expander("View Analysis Code"):
                            st.code(result.analysis_code, language="python")
                else:
                    st.info("No analysis performed")
            
            with tabs[3]:
                if result.visualization_path and os.path.exists(result.visualization_path):
                    st.image(result.visualization_path, use_column_width=True)
                    if result.visualization_code:
                        with st.expander("View Visualization Code"):
                            st.code(result.visualization_code, language="python")
                else:
                    st.info("No visualization created")


if __name__ == "__main__":
    main()
