"""
Communication Agent - Natural Language Response Synthesis

This agent is responsible for converting technical outputs (SQL results, analysis,
visualizations) into clear, user-friendly natural language responses.

Key responsibilities:
- Safe DataFrame handling (avoid ambiguity errors)
- Summarize data insights
- Explain what was found
- Suggest next steps
- Synthesize results from multiple agents
"""

import pandas as pd
from typing import Any, Optional
from langchain_core.prompts import ChatPromptTemplate

from src.agents.base import BaseAgent, AgentState
from src.config import Config
from src.utils.llm_factory import get_llm


class CommunicationAgent(BaseAgent):
    """Agent for synthesizing natural language responses from technical outputs."""
    
    def __init__(self, config: Config):
        """Initialize the communication agent."""
        super().__init__(config)
        self.llm = get_llm()
        
        # System prompt for response synthesis
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a communication specialist in a data analytics system.
Your job is to translate technical outputs into clear, conversational responses.

Guidelines:
1. Be conversational and friendly, not robotic
2. Summarize key findings at the top
3. Provide relevant data details
4. Highlight interesting insights or patterns
5. Suggest logical next steps when appropriate
6. Use bullet points for multiple findings
7. Keep responses concise but informative
8. Avoid technical jargon unless necessary

Context about what happened:
- Query: {query}
- Agents executed: {agent_chain}
- SQL executed: {sql_executed}

Available information:
{data_summary}

Your task: Synthesize this into a natural, helpful response for the user."""),
            ("user", "Create a response that answers the user's question: {query}")
        ])
    
    def execute(self, state: AgentState) -> AgentState:
        """
        Generate natural language response from state.
        
        Args:
            state: Current agent state with query results
            
        Returns:
            Updated state with final_response
        """
        # Use retry wrapper for execution
        return self.execute_with_retry(state, self._execute_impl)
    
    def _execute_impl(self, state: AgentState) -> AgentState:
        """Implementation of communication execution (wrapped in retry logic)."""
        try:
            # Build data summary from available information
            data_summary = self._build_data_summary(state)
            
            # Get agent chain for context
            agent_chain = ", ".join(state.agent_chain) if hasattr(state, 'agent_chain') and state.agent_chain else "SQL Agent"
            
            # Check if SQL was executed
            sql_executed = "Yes" if state.sql_query else "No"
            
            # Generate response using LLM
            chain = self.prompt | self.llm
            
            response = chain.invoke({
                "query": state.query,
                "agent_chain": agent_chain,
                "sql_executed": sql_executed,
                "data_summary": data_summary
            })
            
            # Update state
            state.final_response = response.content
            state.agent_chain.append("communication_agent")
            
        except Exception as e:
            # Re-raise so retry logic can handle it
            raise
        
        return state
    
    def _build_data_summary(self, state: AgentState) -> str:
        """
        Build a comprehensive summary of all available data.
        Safely handles DataFrames to avoid ambiguity errors.
        
        Args:
            state: Agent state with various results
            
        Returns:
            String summary of all findings
        """
        sections = []
        
        # 1. SQL Query Results (check both query_results and cached_dataframe)
        data_source = None
        if state.query_results is not None:
            data_source = state.query_results
        elif state.cached_dataframe is not None:
            data_source = state.cached_dataframe
            print("[CommunicationAgent] Using cached_dataframe as data source")
        
        if data_source is not None:
            sections.append(self._summarize_query_results(data_source))
        
        # 2. Analysis Results
        if state.analysis_results:
            sections.append(f"Analysis Findings:\n{state.analysis_results}")
        
        # 3. Visualization Info
        if state.visualization_paths:
            viz_info = f"Visualizations created: {', '.join(state.visualization_paths)}"
            sections.append(viz_info)
        
        # 4. Errors (if any)
        if state.errors:
            error_info = f"Note: Some issues occurred: {'; '.join(state.errors)}"
            sections.append(error_info)
        
        # 5. Result summary (if already set by other agents)
        if hasattr(state, 'result_summary') and state.result_summary:
            sections.append(f"Summary: {state.result_summary}")
        
        return "\n\n".join(sections) if sections else "No data available"
    
    def _summarize_query_results(self, query_results: Any) -> str:
        """
        Safely summarize query results, handling DataFrames properly.
        
        Args:
            query_results: Results from SQL query (DataFrame, list, dict, etc.)
            
        Returns:
            String summary of results
        """
        try:
            # Handle pandas DataFrame
            if isinstance(query_results, pd.DataFrame):
                return self._summarize_dataframe(query_results)
            
            # Handle list of results
            elif isinstance(query_results, list):
                if len(query_results) == 0:
                    return "Query Results: No data found"
                return f"Query Results: {len(query_results)} rows returned\n{str(query_results[:5])}"
            
            # Handle dict
            elif isinstance(query_results, dict):
                return f"Query Results:\n{str(query_results)}"
            
            # Handle string or other types
            else:
                return f"Query Results:\n{str(query_results)}"
                
        except Exception as e:
            return f"Query Results: [Error summarizing: {e}]"
    
    def _summarize_dataframe(self, df: pd.DataFrame) -> str:
        """
        Create a comprehensive summary of a DataFrame.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            String summary with shape, columns, sample data
        """
        if df.empty:
            return "Query Results: Empty result set (no rows returned)"
        
        summary_parts = [
            f"Query Results: {len(df)} rows, {len(df.columns)} columns",
            f"Columns: {', '.join(df.columns.tolist())}",
        ]
        
        # Add sample data (first few rows)
        if len(df) <= 10:
            summary_parts.append(f"Data:\n{df.to_string()}")
        else:
            summary_parts.append(f"Sample (first 5 rows):\n{df.head().to_string()}")
            summary_parts.append(f"... (showing 5 of {len(df)} rows)")
        
        # Add basic statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0 and len(numeric_cols) <= 5:
            summary_parts.append(f"\nNumeric Summary:\n{df[numeric_cols].describe().to_string()}")
        
        return "\n".join(summary_parts)
    
    def _create_fallback_response(self, state: AgentState) -> str:
        """
        Create a basic fallback response when LLM synthesis fails.
        
        Args:
            state: Agent state
            
        Returns:
            Simple fallback response string
        """
        parts = [f"I processed your query: '{state.query}'"]
        
        if state.query_results is not None:
            if isinstance(state.query_results, pd.DataFrame):
                if not state.query_results.empty:
                    parts.append(f"Found {len(state.query_results)} rows of data.")
                else:
                    parts.append("No data found.")
            else:
                parts.append("Retrieved results from the database.")
        
        if state.analysis_results:
            parts.append("Performed statistical analysis.")
        
        if state.visualization_paths:
            parts.append(f"Created {len(state.visualization_paths)} visualization(s).")
        
        if state.errors:
            parts.append(f"Note: Encountered {len(state.errors)} issue(s) during processing.")
        
        return " ".join(parts)
