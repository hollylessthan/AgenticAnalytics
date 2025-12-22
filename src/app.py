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
                st.dataframe(result.query_results, width='stretch')
                
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
        
        # Show generated code in expandable sections
        code_sections = []
        
        if result.sql_query:
            code_sections.append(("🔍 SQL Query", result.sql_query, "sql"))
        if result.profiling_code:
            code_sections.append(("📋 Profiling Code", result.profiling_code, "python"))
        if result.preprocessing_code:
            code_sections.append(("🔧 Preprocessing Code", result.preprocessing_code, "python"))
        if result.analysis_code:
            code_sections.append(("📊 Analysis Code", result.analysis_code, "python"))
        if result.modeling_code:
            code_sections.append(("🤖 Modeling Code", result.modeling_code, "python"))
        if result.visualization_code:
            code_sections.append(("📈 Viz Code", result.visualization_code, "python"))
        
        # Display code sections dynamically based on what's available
        if code_sections:
            num_sections = len(code_sections)
            if num_sections <= 3:
                cols = st.columns(num_sections)
            else:
                # If more than 3, use 3 columns and wrap
                cols = st.columns(3)
            
            for i, (title, code, lang) in enumerate(code_sections):
                col_idx = i % 3 if num_sections > 3 else i
                with cols[col_idx].expander(title, expanded=False):
                    st.code(code, language=lang)


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
        
        # Preprocessing Configuration (NEW)
        st.subheader("🔧 Data Preprocessing")
        
        preprocessing_mode = st.radio(
            "Preprocessing Mode",
            options=["confirm", "auto", "manual"],
            index=0 if st.session_state.get("preprocessing_mode", "confirm") == "confirm" else 
                  (1 if st.session_state.get("preprocessing_mode", "confirm") == "auto" else 2),
            help="""
            • **Confirm** (Recommended): Ask before applying preprocessing steps
            • **Auto**: Automatically apply safe preprocessing for modeling
            • **Manual**: No preprocessing unless explicitly requested
            """
        )
        
        if preprocessing_mode == "confirm":
            st.info("✓ Will ask for confirmation before preprocessing")
        elif preprocessing_mode == "auto":
            st.warning("⚡ Auto-applying preprocessing for modeling tasks")
        else:
            st.info("📝 Manual mode - no automatic preprocessing")
        
        # Update session state
        if st.session_state.get("preprocessing_mode") != preprocessing_mode:
            st.session_state.preprocessing_mode = preprocessing_mode
        
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
    
    # Check if we need preprocessing reuse confirmation (NEW)
    if hasattr(st.session_state, 'previous_state') and st.session_state.previous_state:
        state = st.session_state.previous_state
        
        # Handle preprocessing reuse confirmation
        if (hasattr(state, 'needs_preprocessing_confirmation') and 
            state.needs_preprocessing_confirmation and 
            hasattr(state, 'preprocessing_reuse_prompt') and
            state.preprocessing_reuse_prompt):
            
            # Display the preprocessing reuse prompt (formatted message from agent)
            st.info(state.preprocessing_reuse_prompt)
            
            # Buttons to proceed or reprocess
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Use Existing Preprocessed Data", type="primary", key="reuse_preproc"):
                    # Approve reuse - continue to modeling
                    state.needs_preprocessing_confirmation = False
                    state.preprocessing_reuse_approved = True
                    st.session_state.previous_state = state
                    st.rerun()
            
            with col2:
                if st.button("🔄 Reprocess from Scratch", key="reprocess"):
                    # Reject reuse - clear cached preprocessing
                    state.needs_preprocessing_confirmation = False
                    state.preprocessing_reuse_approved = False
                    state.preprocessed_dataframe = None
                    state.preprocessing_applied = []
                    st.session_state.previous_state = state
                    st.rerun()
            
            # Don't process new input while waiting for confirmation
            return
        
        # Handle preprocessing reuse confirmation (NEW: for cached preprocessing data)
        if (hasattr(state, 'needs_preprocessing_confirmation') and 
            state.needs_preprocessing_confirmation and
            hasattr(state, 'preprocessing_reuse_prompt') and
            state.preprocessing_reuse_prompt):
            
            # Show the preprocessing reuse prompt (shows transformations + data preview)
            st.warning("🔧 **Preprocessed Data Available**")
            st.markdown(state.preprocessing_reuse_prompt)
            
            # Buttons to reuse or reprocess
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Use Existing Preprocessed Data", type="primary"):
                    # Continue with existing preprocessing
                    state.needs_preprocessing_confirmation = False
                    state.preprocessing_approved = True  # Signal to continue
                    st.session_state.previous_state = state
                    st.rerun()
            
            with col2:
                if st.button("🔄 Reprocess from Scratch"):
                    # Clear preprocessing and rerun
                    state.preprocessed_dataframe = None
                    state.preprocessing_applied = []
                    state.data_profile = None
                    state.needs_preprocessing_confirmation = False
                    st.session_state.previous_state = state
                    st.rerun()
            
            # Don't process new input while waiting for confirmation
            return
        
        # Handle preprocessing confirmation (persists across reruns via session state)
        if hasattr(st.session_state, 'pending_preprocessing') and st.session_state.pending_preprocessing:
            state = st.session_state.previous_state
            
            if (hasattr(state, 'needs_preprocessing_confirmation') and 
                state.needs_preprocessing_confirmation and 
                hasattr(state, 'preprocessing_needed') and
                state.preprocessing_needed):
                
                # Show preprocessing confirmation dialog
                st.warning("**Data Preprocessing Recommended**")
                st.write("The following preprocessing steps are recommended for better analysis:")
                
                # Show data preview
                data_source = None
                if hasattr(state, 'preprocessed_dataframe') and state.preprocessed_dataframe is not None:
                    data_source = state.preprocessed_dataframe
                elif hasattr(state, 'query_results') and state.query_results is not None:
                    data_source = state.query_results
                elif hasattr(state, 'cached_dataframe') and state.cached_dataframe is not None:
                    data_source = state.cached_dataframe
                
                if data_source is not None:
                    import pandas as pd
                    if isinstance(data_source, pd.DataFrame):
                        df = data_source
                    else:
                        df = pd.DataFrame(data_source)
                    
                    st.write(f"**Data Preview** ({len(df)} rows, {len(df.columns)} columns)")
                    st.dataframe(df.head(10), use_container_width=True)
                
                recommendations = state.preprocessing_needed.get("recommendations", [])
                
                # Show summary
                if recommendations:
                    st.info(f"**{len(recommendations)} preprocessing steps recommended**")
                
                # Allow user to select which preprocessing steps to apply
                st.write("**Select preprocessing steps to apply:**")
                selected_actions = []
                
                for idx, rec in enumerate(recommendations):
                    action = rec["action"]
                    reason = rec["reason"]
                    suggestion = rec["suggestion"]
                    impact = rec["impact"]
                    details = rec.get("details", "")
                    
                    # Create checkbox with expandable details
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        label = f"**{action.replace('_', ' ').title()}** - {reason}"
                        is_selected = st.checkbox(label, value=True, key=f"prep_{action}_{idx}")
                        if is_selected:
                            selected_actions.append(action)
                    
                    with col2:
                        with st.expander("Details"):
                            st.write(f"**Suggestion:** {suggestion}")
                            st.write(f"**Impact:** {impact}")
                            if details:
                                st.write(f"**Details:** {details}")
                
                # Store selected actions in session state for persistence
                st.session_state.selected_preprocessing_actions = selected_actions
                
                # Buttons to proceed or cancel
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Apply Selected Preprocessing", type="primary"):
                        # Get the selected actions from session state
                        approved_actions = st.session_state.get('selected_preprocessing_actions', [])
                        
                        # Update state with approved preprocessing
                        state.preprocessing_approved = approved_actions
                        state.needs_preprocessing_confirmation = False
                        st.session_state.pending_preprocessing = False
                        
                        print(f"[DEBUG] Approved preprocessing actions: {approved_actions}")
                        
                        # Continue execution by re-running orchestrator
                        try:
                            # Continue from where we left off
                            result = st.session_state.orchestrator.run(
                                state.query,
                                st.session_state.get('conversation_history', []),
                                previous_state=state
                            )
                            
                            # Add response to messages
                            response = result.final_answer or result.final_response or "Preprocessing applied successfully."
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response,
                                "result": result
                            })
                            
                            # Store results
                            st.session_state.last_result = result
                            st.session_state.previous_state = result
                            
                            # Clean up
                            del st.session_state.selected_preprocessing_actions
                            
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error continuing after preprocessing: {e}")
                            st.session_state.pending_preprocessing = False
                            return
                
                with col2:
                    if st.button("Skip Preprocessing"):
                        # Skip all preprocessing
                        state.preprocessing_approved = []
                        state.needs_preprocessing_confirmation = False
                        st.session_state.pending_preprocessing = False
                        st.session_state.previous_state = state
                        st.rerun()
                
                # Don't process new input while waiting for confirmation
                return
    
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
            
            # Get preprocessing mode from session state
            preprocessing_mode = st.session_state.get('preprocessing_mode', 'confirm')
            
            if previous_state:
                # Preserve metadata across turns
                previous_state.metadata.update(metadata)
                # Update preprocessing mode
                previous_state.preprocessing_mode = preprocessing_mode
                result = st.session_state.orchestrator.run(
                    user_input,
                    conversation_history,
                    previous_state=previous_state
                )
            else:
                # First query - create new state with metadata
                from src.agents.base import AgentState
                initial_state = AgentState(
                    query=user_input, 
                    metadata=metadata,
                    preprocessing_mode=preprocessing_mode
                )
                result = st.session_state.orchestrator.run(
                    user_input,
                    conversation_history,
                    previous_state=initial_state
                )
                
            # Clear status display
            status_placeholder.empty()
            
            # Add to conversation snapshot history
            result.add_snapshot()
            
            # DEBUG: Check preprocessing confirmation state
            print(f"[DEBUG] needs_preprocessing_confirmation: {getattr(result, 'needs_preprocessing_confirmation', False)}")
            print(f"[DEBUG] preprocessing_needed exists: {hasattr(result, 'preprocessing_needed')}")
            print(f"[DEBUG] preprocessing_approved: {getattr(result, 'preprocessing_approved', None)}")
            
            # CHECK FOR PREPROCESSING CONFIRMATION BEFORE DISPLAYING RESULT
            # Handle preprocessing confirmation (fresh preprocessing, not reuse)
            if (hasattr(result, 'needs_preprocessing_confirmation') and 
                result.needs_preprocessing_confirmation and 
                hasattr(result, 'preprocessing_needed') and
                result.preprocessing_needed):
                
                # Only show dialog if not already approved (None or empty list)
                preprocessing_approved = getattr(result, 'preprocessing_approved', None)
                if not preprocessing_approved:  # Handles None, [], or False
                    print("[DEBUG] Showing preprocessing confirmation dialog")
                    
                    # Store result for later use (CRITICAL: must persist across reruns)
                    st.session_state.previous_state = result
                    st.session_state.pending_preprocessing = True
                    
                    # Don't add message to history while waiting for confirmation
                    # The dialog will be shown below
            
            # Store results for display
            st.session_state.last_result = result
            if not hasattr(st.session_state, 'pending_preprocessing') or not st.session_state.pending_preprocessing:
                st.session_state.previous_state = result  # For stateful conversation (includes full state_history)
            
            # Add assistant response with result metadata
            # Don't show error message when preprocessing confirmation is pending
            if hasattr(result, 'needs_preprocessing_confirmation') and result.needs_preprocessing_confirmation:
                # Preprocessing confirmation is pending - don't add any message
                pass
            else:
                # Check both final_answer and final_response for backward compatibility
                response = result.final_answer or result.final_response or "I couldn't process your request."
                
                # Check for agent-specific errors
                if result.errors and len(result.errors) > 0:
                    # Show agent errors as warnings
                    for error in result.errors:
                        error_text = str(error) if not isinstance(error, str) else error
                        st.warning(error_text)
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
            
            # Get full error details for debugging
            error_str = str(e)
            traceback_str = traceback.format_exc()
            
            # Provide more context based on error type
            if "visualization_agent" in error_str.lower():
                error_msg = f"❌ Visualization Agent Error\n\n{error_str}"
            elif "sql" in error_str.lower():
                error_msg = f"❌ SQL Query Error\n\n{error_str}"
            elif "analysis" in error_str.lower():
                error_msg = f"❌ Analysis Agent Error\n\n{error_str}"
            else:
                error_msg = f"❌ Error: {error_str}"
            
            st.error(error_msg)
            with st.expander("📋 Full Error Details (for debugging)"):
                st.code(traceback_str, language="python")
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        st.rerun()


if __name__ == "__main__":
    main()
