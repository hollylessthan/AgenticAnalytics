"""Agent orchestrator using LangGraph."""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate

from .base import AgentState
from .sql_agent import SQLAgent
from .analysis_agent import AnalysisAgent
from .visualization_agent import VisualizationAgent
from ..config import config
from ..utils.llm_factory import get_llm


class AgentOrchestrator:
    """Orchestrates multiple agents using LangGraph."""
    
    def __init__(self, llm=None):
        """Initialize the orchestrator.
        
        Args:
            llm: Optional LLM instance (uses factory if not provided)
        """
        self.llm = llm or get_llm()
        
        # Initialize agents
        self.sql_agent = SQLAgent(self.llm)
        self.analysis_agent = AnalysisAgent(self.llm)
        self.visualization_agent = VisualizationAgent(self.llm)
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the agent workflow graph.
        
        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("planner", self._plan_execution)
        workflow.add_node("sql_agent", self.sql_agent.execute)
        workflow.add_node("analysis_agent", self.analysis_agent.execute)
        workflow.add_node("visualization_agent", self.visualization_agent.execute)
        workflow.add_node("finalizer", self._finalize_response)
        
        # Set entry point
        workflow.set_entry_point("planner")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "planner",
            self._route_from_planner,
            {
                "sql": "sql_agent",
                "analysis": "analysis_agent",
                "visualization": "visualization_agent",
                "end": "finalizer"
            }
        )
        
        workflow.add_conditional_edges(
            "sql_agent",
            self._route_from_sql,
            {
                "analysis": "analysis_agent",
                "visualization": "visualization_agent",
                "finalizer": "finalizer",
                "error": "finalizer"
            }
        )
        
        workflow.add_conditional_edges(
            "analysis_agent",
            self._route_from_analysis,
            {
                "visualization": "visualization_agent",
                "finalizer": "finalizer",
                "error": "finalizer"
            }
        )
        
        workflow.add_edge("visualization_agent", "finalizer")
        workflow.add_edge("finalizer", END)
        
        return workflow.compile()
    
    def _plan_execution(self, state: AgentState) -> AgentState:
        """Plan which agents to use based on user query.
        
        Args:
            state: Current state
            
        Returns:
            Updated state with next agent
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a planning agent that determines which specialized agents to use.
            
Available agents:
- sql_agent: Converts natural language to SQL queries and retrieves data
- analysis_agent: Performs data analysis using Python
- visualization_agent: Creates visualizations from data

Analyze the user query and determine which agent should be used first.
If the query requires data from a database, start with sql_agent.
If the query is about analyzing existing data, start with analysis_agent.
If the query is about creating a visualization, determine if data needs to be retrieved first.

Respond with only one word: sql, analysis, visualization, or end."""),
            ("user", "{query}")
        ])
        
        response = self.llm.invoke(prompt.format_messages(query=state.user_query))
        next_agent = response.content.strip().lower()
        
        state.next_agent = next_agent
        state.metadata["plan"] = next_agent
        
        return state
    
    def _route_from_planner(self, state: AgentState) -> str:
        """Route from planner to appropriate agent.
        
        Args:
            state: Current state
            
        Returns:
            Next agent name
        """
        next_agent = state.next_agent or "end"
        return next_agent
    
    def _route_from_sql(self, state: AgentState) -> str:
        """Route from SQL agent.
        
        Args:
            state: Current state
            
        Returns:
            Next node name
        """
        if state.errors:
            return "error"
        
        if state.next_agent == "analysis":
            return "analysis"
        elif state.next_agent == "visualization":
            return "visualization"
        else:
            return "finalizer"
    
    def _route_from_analysis(self, state: AgentState) -> str:
        """Route from analysis agent.
        
        Args:
            state: Current state
            
        Returns:
            Next node name
        """
        if state.errors:
            return "error"
        
        if state.next_agent == "visualization":
            return "visualization"
        else:
            return "finalizer"
    
    def _finalize_response(self, state: AgentState) -> AgentState:
        """Generate final response to user.
        
        Args:
            state: Current state
            
        Returns:
            Updated state with final answer
        """
        if state.errors:
            state.final_answer = f"I encountered errors while processing your request:\n" + "\n".join(state.errors)
            return state
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data analyst assistant. Generate a clear, concise response to the user's query based on the results.
            
Include:
- Summary of what was done
- Key findings from the data
- Any visualizations created
- Actionable insights if applicable

Be professional but conversational."""),
            ("user", """User Query: {query}

SQL Query: {sql_query}
Query Results: {results}
Analysis Results: {analysis}
Visualization: {viz}

Generate a comprehensive response.""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            query=state.user_query,
            sql_query=state.sql_query or "N/A",
            results=str(state.query_results)[:500] if state.query_results else "N/A",
            analysis=str(state.analysis_results) if state.analysis_results else "N/A",
            viz=state.visualization_path or "N/A"
        ))
        
        state.final_answer = response.content
        return state
    
    def run(self, user_query: str, conversation_history: list = None) -> AgentState:
        """Run the orchestrator with a user query.
        
        Args:
            user_query: User's natural language query
            conversation_history: Previous conversation messages
            
        Returns:
            Final agent state
        """
        initial_state = AgentState(
            user_query=user_query,
            conversation_history=conversation_history or []
        )
        
        final_state = self.graph.invoke(initial_state)
        return final_state
