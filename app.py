"""Streamlit application for Agentic Analytics."""

import os
import streamlit as st
import pandas as pd
from pathlib import Path
from agentic_analytics.orchestrator import AgenticOrchestrator
from agentic_analytics.utils.database import get_schema_info, create_sample_database
from agentic_analytics.config.settings import settings

# Page configuration
st.set_page_config(
    page_title="Agentic Analytics",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None


def initialize_system():
    """Initialize the agentic analytics system."""
    # Ensure data directory exists
    data_dir = Path("data/examples")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample database if it doesn't exist
    db_path = settings.database_path
    if not os.path.exists(db_path):
        st.info("Creating sample database...")
        create_sample_database(db_path)
    
    # Get schema
    schema = get_schema_info(db_path)
    
    # Initialize orchestrator
    orchestrator = AgenticOrchestrator(db_path, schema)
    
    return orchestrator, schema


def main():
    """Main application function."""
    st.title("🤖 Agentic Analytics")
    st.subheader("Multi-Agent Data Analyst Chatbot")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=settings.openai_api_key,
            help="Enter your OpenAI API key"
        )
        
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            settings.openai_api_key = api_key
        
        # Database info
        st.header("📊 Database Info")
        db_path = st.text_input("Database Path", value=settings.database_path)
        
        if st.button("🔄 Initialize System"):
            with st.spinner("Initializing..."):
                try:
                    orchestrator, schema = initialize_system()
                    st.session_state.orchestrator = orchestrator
                    st.success("✅ System initialized!")
                    
                    with st.expander("📋 Database Schema"):
                        st.code(schema)
                except Exception as e:
                    st.error(f"❌ Initialization failed: {str(e)}")
        
        # About
        st.header("ℹ️ About")
        st.markdown("""
        This chatbot uses multiple AI agents to:
        - 📝 Convert questions to SQL
        - 🔍 Retrieve data
        - 📊 Analyze results
        - 📈 Create visualizations
        
        Powered by:
        - LangChain & LangGraph
        - OpenAI GPT-4
        - Streamlit
        - FAISS/Weaviate
        """)
    
    # Main chat interface
    st.markdown("---")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display data if available
            if "data" in message and message["data"] is not None:
                with st.expander("📊 View Data"):
                    st.dataframe(message["data"])
            
            # Display figure if available
            if "figure" in message and message["figure"] is not None:
                st.plotly_chart(message["figure"], use_container_width=True)
            
            # Display SQL if available
            if "sql" in message and message["sql"]:
                with st.expander("🔍 SQL Query"):
                    st.code(message["sql"], language="sql")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your data..."):
        # Check if system is initialized
        if not st.session_state.orchestrator:
            st.warning("⚠️ Please initialize the system first using the sidebar.")
            return
        
        # Check API key
        if not settings.openai_api_key:
            st.warning("⚠️ Please enter your OpenAI API key in the sidebar.")
            return
        
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    # Run orchestrator
                    result = st.session_state.orchestrator.run(prompt)
                    
                    # Extract results
                    analysis = result.get("analysis", "")
                    final_response = result.get("final_response", analysis)
                    data = result.get("data")
                    figure = result.get("figure")
                    sql_query = result.get("sql_query", "")
                    messages = result.get("messages", [])
                    
                    # Display response
                    response_text = final_response if final_response else "I've processed your request."
                    st.markdown(response_text)
                    
                    # Show execution steps
                    if messages:
                        with st.expander("🔍 Execution Steps"):
                            for msg in messages:
                                st.text(msg)
                    
                    # Display data
                    if data is not None and isinstance(data, pd.DataFrame) and not data.empty:
                        with st.expander("📊 View Data"):
                            st.dataframe(data)
                    
                    # Display figure
                    if figure is not None:
                        st.plotly_chart(figure, use_container_width=True)
                    
                    # Display SQL
                    if sql_query:
                        with st.expander("🔍 SQL Query"):
                            st.code(sql_query, language="sql")
                    
                    # Add assistant message to chat
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "data": data,
                        "figure": figure,
                        "sql": sql_query
                    })
                    
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
    
    # Example questions
    if len(st.session_state.messages) == 0:
        st.markdown("### 💡 Example Questions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            - What are the total sales by product?
            - Show me the top 3 selling products
            - What's the average price by category?
            """)
        
        with col2:
            st.markdown("""
            - Create a bar chart of sales by product
            - Analyze the distribution of product prices
            - Show me sales trends over time
            """)


if __name__ == "__main__":
    main()
