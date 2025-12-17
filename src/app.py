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
from src.utils.session_tables import SessionTableManager
from src.config import config


# Page configuration
st.set_page_config(
    page_title="Data Copilot",
    page_icon="🐶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    """Load custom CSS from file."""
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")
    with open(css_path, "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css()


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
    
    # Smart Limit settings
    if "smart_limit" not in st.session_state:
        st.session_state.smart_limit = True
    if "smart_limit_rows" not in st.session_state:
        st.session_state.smart_limit_rows = 1000
    
    # Session Table Manager
    if "table_manager" not in st.session_state:
        st.session_state.table_manager = None  # Will be initialized when database is connected
    
    # Track pinned table names separately (for persistence across reruns)
    if "pinned_table_names" not in st.session_state:
        st.session_state.pinned_table_names = []


def initialize_systems():
    """Initialize agent orchestrator and RAG system."""
    try:
        if st.session_state.orchestrator is None:
            with st.spinner("Initializing Agent Orchestrator..."):
                st.session_state.orchestrator = AgentOrchestrator(
                    smart_limit=st.session_state.smart_limit,
                    smart_limit_rows=st.session_state.smart_limit_rows
                )
        
        # Always initialize table manager if orchestrator exists but table_manager doesn't
        if st.session_state.orchestrator and st.session_state.table_manager is None:
            sql_agent = st.session_state.orchestrator.sql_agent
            if sql_agent and hasattr(sql_agent, 'db'):
                st.session_state.table_manager = SessionTableManager(sql_agent.db)
        
        if st.session_state.rag_system is None:
            with st.spinner("Initializing RAG System..."):
                st.session_state.rag_system = RAGSystem()
                # Try to load existing index
                try:
                    st.session_state.rag_system.load_index()
                except Exception as load_error:
                    # Index doesn't exist yet, will create on first use
                    pass
                
                # Auto-index database schema on first initialization
                try:
                    from src.utils.database import DatabaseManager
                    db = DatabaseManager()
                    schema = db.get_schema_info()
                    with st.spinner("Indexing database schema..."):
                        st.session_state.rag_system.index_database_schema(schema)
                        st.session_state.rag_system.save_index()
                except Exception as index_error:
                    # If indexing fails, continue - RAG will still work but without schema optimization
                    pass
        
        return True
    except Exception as e:
        import traceback
        st.error(f"Failed to initialize systems: {str(e)}")
        st.error("Please check your .env file and ensure all required API keys are set.")
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
        return False


def display_chat_message(role: str, content: str, result=None, message=None):
    """Display a chat message with optional inline results.
    
    Args:
        role: 'user' or 'assistant'
        content: Message content
        result: Optional AgentState result for inline display
        message: Optional full message dict with pinned_table info
        result: Optional AgentState result for inline display
    """
    import pandas as pd
    from datetime import datetime
    
    css_class = "user-message" if role == "user" else "assistant-message"
    icon = "👤" if role == "user" else "🤖"
    
    # Display message text
    st.markdown(f"""
    <div class="chat-message {css_class}">
        <strong>{icon} {role.capitalize()}</strong><br/>
        {content}
    </div>
    """, unsafe_allow_html=True)
    
    # Display inline results if available
    if result and role == "assistant":
        # Show DataFrame inline
        if result.query_results is not None and isinstance(result.query_results, pd.DataFrame):
            with st.expander(f"📊 Data Preview ({len(result.query_results)} rows)", expanded=False):
                st.dataframe(result.query_results, use_container_width=True)
                
                # Action buttons row
                col1, col2, col3, col4 = st.columns(4)
                
                # Download CSV
                with col1:
                    csv = result.query_results.to_csv(index=False)
                    st.download_button(
                        label="📥 CSV",
                        data=csv,
                        file_name=f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key=f"csv_{id(result)}"
                    )
                
                # Download Excel
                with col2:
                    try:
                        from io import BytesIO
                        buffer = BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            result.query_results.to_excel(writer, index=False, sheet_name='Data')
                        buffer.seek(0)
                        
                        st.download_button(
                            label="📥 Excel",
                            data=buffer,
                            file_name=f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"xlsx_{id(result)}"
                        )
                    except ImportError:
                        pass  # openpyxl not installed
                

        
        # Show visualization inline
        if result.visualization_path and os.path.exists(result.visualization_path):
            with st.expander("📈 Visualization", expanded=True):
                st.image(result.visualization_path, use_column_width=True)
                
                # Download button for image
                with open(result.visualization_path, "rb") as file:
                    st.download_button(
                        label="📥 Download Image",
                        data=file,
                        file_name=f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        mime="image/png",
                        key=f"img_{id(result)}"
                    )
        
        # Show SQL query if available
        if result.sql_query:
            with st.expander("🔍 SQL Query", expanded=False):
                # Display with light background for better readability
                st.markdown("""
                <style>
                .sql-code {
                    background-color: #f8f8f8;
                    color: #2d3436;
                    padding: 1rem;
                    border-radius: 0.5rem;
                    border: 1px solid #e0e0e0;
                    overflow-x: auto;
                    font-family: 'Courier New', monospace;
                    font-size: 0.9rem;
                    line-height: 1.5;
                }
                </style>
                """, unsafe_allow_html=True)
                st.code(result.sql_query, language="sql")


def main():
    """Main application."""
    # Initialize
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">Data Copilot</h1>', unsafe_allow_html=True)
    st.markdown("**An agent-assisted interface for querying, analyzing, visualizing, and validating analytical data.**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # System status - auto-initialized
        st.subheader("System Status")
        
        # Initialize systems on app load
        if st.session_state.orchestrator is None or st.session_state.rag_system is None:
            with st.spinner("🔄 Initializing systems..."):
                if initialize_systems():
                    st.success("✅ Orchestrator & RAG initialized")
                else:
                    st.error("❌ Failed to initialize systems")
        else:
            st.success("✅ Systems ready")
            
            # Show reinitialize button only if needed
            if st.button("🔄 Reinitialize Systems"):
                st.session_state.orchestrator = None
                st.session_state.rag_system = None
                st.rerun()
        
        # Display configuration
        st.subheader("Configuration")
        st.text(f"Model: {config.agent_model}")
        st.text(f"Vector Store: {config.vector_store_type}")
        st.text(f"Database: {config.database_url.split('://')[0]}")
        
        st.divider()
        
        # Query Optimization
        st.subheader("⚡ Query Optimization")
        
        smart_limit = st.checkbox(
            "Smart LIMIT (Recommended)",
            value=st.session_state.smart_limit,
            help="Automatically add LIMIT to queries without one. Improves performance and prevents huge result sets."
        )
        
        if smart_limit:
            smart_limit_rows = st.slider(
                "Default LIMIT",
                min_value=100,
                max_value=10000,
                value=st.session_state.smart_limit_rows,
                step=100,
                help="Default row limit for queries"
            )
            st.success(f"✓ Queries will be limited to {smart_limit_rows:,} rows (unless query has explicit LIMIT)")
        else:
            smart_limit_rows = st.session_state.smart_limit_rows
            st.warning("⚠️ Queries may return unlimited rows. This can be slow and memory-intensive.")
        
        # Update session state and reinitialize if changed
        if (smart_limit != st.session_state.smart_limit or 
            smart_limit_rows != st.session_state.smart_limit_rows):
            st.session_state.smart_limit = smart_limit
            st.session_state.smart_limit_rows = smart_limit_rows
            # Force reinitialize orchestrator with new settings
            st.session_state.orchestrator = None
            st.info("Settings updated. Orchestrator will reinitialize on next query.")
        
        st.divider()
        
        # Cache Configuration
        st.subheader("💾 Cache Settings")
        
        cache_enabled = st.checkbox(
            "Enable Data Caching",
            value=config.enable_data_cache,
            help="Cache query results for faster follow-up questions"
        )
        
        if cache_enabled:
            col_a, col_b = st.columns(2)
            with col_a:
                max_rows = st.number_input(
                    "Max Rows",
                    min_value=1000,
                    max_value=1000000,
                    value=config.max_cache_rows,
                    step=1000,
                    help="Maximum rows to cache"
                )
            with col_b:
                max_mb = st.number_input(
                    "Max Size (MB)",
                    min_value=10,
                    max_value=10000,
                    value=config.max_cache_size_mb,
                    step=10,
                    help="Maximum cache size in MB"
                )
            
            auto_sample = st.checkbox(
                "Auto-Sample Large Results",
                value=config.auto_sample_large_results,
                help="⚠️ When enabled, large datasets exceeding limits will be randomly sampled. Analysis will run on sample, not full data."
            )
            
            if auto_sample:
                sample_size = st.number_input(
                    "Sample Size (rows)",
                    min_value=100,
                    max_value=100000,
                    value=config.sample_size,
                    step=100,
                    help="Number of rows to keep when sampling"
                )
                st.warning("⚠️ Auto-sampling is ON. Large results will be sampled for caching.")
            else:
                sample_size = config.sample_size
                st.info("ℹ️ Large results exceeding limits will NOT be cached.")
            
            # Update config
            config.enable_data_cache = cache_enabled
            config.max_cache_rows = max_rows
            config.max_cache_size_mb = max_mb
            config.auto_sample_large_results = auto_sample
            config.sample_size = sample_size
            
            # Display cache status
            if hasattr(st.session_state, 'last_result') and st.session_state.last_result:
                cache_info = st.session_state.last_result.metadata.get('cache_info', {})
                if cache_info.get('has_cache'):
                    st.success(f"✓ Data cached: {cache_info['row_count']:,} rows ({cache_info['size_mb']:.1f} MB)")
                    if cache_info.get('is_sampled'):
                        st.warning(f"⚠️ Sampled from {cache_info['original_row_count']:,} rows")
        else:
            config.enable_data_cache = False
        
        st.divider()
        
        # Conversation History Info
        st.subheader("📝 Conversation Memory")
        st.info(f"""
        **Last 10 turns saved automatically**
        
        You can reference previous data:
        - "use original data"
        - "from step 2"  
        - "drill down first table"
        """)
        
        st.divider()
        
        # RAG Status
        st.subheader("📚 RAG System")
        
        if st.session_state.rag_system:
            # Check if index exists
            try:
                has_index = st.session_state.rag_system.index is not None
                if has_index:
                    st.success("✅ RAG index ready")
                else:
                    st.info("ℹ️ RAG system initialized")
            except:
                st.info("ℹ️ RAG system initialized")
            
            # Option to reindex schema if needed
            if st.button("🔄 Reindex Database Schema"):
                try:
                    from src.utils.database import DatabaseManager
                    db = DatabaseManager()
                    schema = db.get_schema_info()
                    with st.spinner("Reindexing schema..."):
                        st.session_state.rag_system.index_database_schema(schema)
                        st.session_state.rag_system.save_index()
                    st.success("✅ Schema reindexed!")
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
    st.subheader("💬 Chat")
    
    # Display chat history
    for message in st.session_state.messages:
        result = message.get("result") if message["role"] == "assistant" else None
        display_chat_message(message["role"], message["content"], result=result, message=message)
    
    # Chat input
    user_input = st.chat_input("Ask me anything about your data...")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Initialize systems if needed
        if not initialize_systems():
            return
        
        # Process query with streaming status
        # Create status placeholder
        status_placeholder = st.empty()
        status_messages = []
        
        def update_status(agent_name: str, message: str, status: str):
            """Callback to update streaming status."""
            # Map agent names to emoji
            agent_icons = {
                "classifier": "🔍",
                "sql_agent": "💾",
                "analysis_agent": "📊",
                "visualization_agent": "📈",
                "communication_agent": "💬"
            }
            icon = agent_icons.get(agent_name, "⚙️")
            
            # Update or add status for this agent
            agent_found = False
            for i, (name, _, _) in enumerate(status_messages):
                if name == agent_name:
                    status_messages[i] = (agent_name, message, status)
                    agent_found = True
                    break
            
            if not agent_found:
                status_messages.append((agent_name, message, status))
            
            # Build status display
            status_html = "<div style='font-family: monospace; font-size: 0.9em;'>"
            for name, msg, st_status in status_messages:
                color = "#28a745" if st_status == "complete" else "#ffc107"
                status_html += f"<div style='color: {color};'>{agent_icons.get(name, '⚙️')} {msg}</div>"
            status_html += "</div>"
            
            status_placeholder.markdown(status_html, unsafe_allow_html=True)
        
        try:
            # Prepare conversation history (text only, no result objects)
            conversation_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.messages[:-1]
            ]
            
            # Prepare metadata with pinned tables schema
            metadata = {}
            if st.session_state.table_manager:
                pinned_schema = st.session_state.table_manager.get_schema_info()
                if pinned_schema:
                    metadata['pinned_tables_schema'] = pinned_schema
            
            # Update orchestrator's status callback (don't reinitialize!)
            if st.session_state.orchestrator:
                st.session_state.orchestrator.status_callback = update_status
            
            # Run orchestrator with stateful conversation support
            previous_state = getattr(st.session_state, 'previous_state', None)
            if previous_state:
                # Preserve metadata across turns
                previous_state.metadata.update(metadata)
                result = st.session_state.orchestrator.run(
                    user_input,
                    conversation_history,
                    previous_state=previous_state
                )
            else:
                # First query - create new state with metadata
                from src.agents.base import AgentState
                initial_state = AgentState(query=user_input, metadata=metadata)
                result = st.session_state.orchestrator.run(
                    user_input,
                    conversation_history,
                    previous_state=initial_state
                )
                
            # Clear status display
            status_placeholder.empty()
            
            # Add to conversation snapshot history
            result.add_snapshot()
            
            # Add assistant response with result metadata
            # Check both final_answer and final_response for backward compatibility
            response = result.final_answer or result.final_response or "I couldn't process your request."
            
            # Check for agent-specific errors
            if result.errors and len(result.errors) > 0:
                # Show agent errors as warnings
                for error in result.errors:
                    st.warning(error)
                # Still show the response if available
                if response != "I couldn't process your request.":
                    st.info(f"Response: {response}")
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "result": result  # Store full result for inline display
                })
            
            # Store results for display
            st.session_state.last_result = result
            st.session_state.previous_state = result  # For stateful conversation (includes full state_history)
            
        except Exception as e:
            status_placeholder.empty()
            import traceback
            
            # Provide more context based on error type
            error_str = str(e)
            if "visualization_agent" in error_str.lower():
                error_msg = "❌ Visualization Agent Error\n\nThe visualization agent encountered an issue. This usually means:\n- No query results were available\n- The query returned empty results\n- The data types were incompatible with the chart type"
            elif "sql" in error_str.lower():
                error_msg = "❌ SQL Query Error\n\nThe SQL agent couldn't generate a valid query. Try:\n- Being more specific about what data you need\n- Checking table/column names\n- Simplifying your request"
            elif "analysis" in error_str.lower():
                error_msg = "❌ Analysis Agent Error\n\nThe analysis agent encountered an issue. Try:\n- Asking a simpler question\n- Providing more context\n- Checking data types"
            else:
                error_msg = f"❌ {error_str}"
            
            st.error(error_msg)
            with st.expander("📋 Error Details"):
                st.code(traceback.format_exc(), language="python")
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        st.rerun()


if __name__ == "__main__":
    main()
