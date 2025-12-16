"""Orchestrator for coordinating multiple agents using LangGraph."""

from typing import Dict, Any, List, TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END
from agentic_analytics.agents.planner_agent import PlannerAgent
from agentic_analytics.agents.sql_agent import SQLAgent
from agentic_analytics.agents.data_agent import DataAgent
from agentic_analytics.agents.analysis_agent import AnalysisAgent
from agentic_analytics.agents.visualization_agent import VisualizationAgent
from agentic_analytics.rag.vector_store import VectorStore
from agentic_analytics.config.settings import settings


class AgentState(TypedDict):
    """State passed between agents."""
    question: str
    plan: List[Dict[str, Any]]
    current_step: int
    schema: str
    database_path: str
    sql_query: str
    data: Any
    analysis: str
    figure: Any
    messages: Annotated[Sequence[str], operator.add]
    final_response: str


class AgenticOrchestrator:
    """Orchestrates multiple agents to answer data analysis questions."""
    
    def __init__(self, database_path: str, schema: str):
        """Initialize the orchestrator.
        
        Args:
            database_path: Path to the SQLite database
            schema: Database schema information
        """
        self.database_path = database_path
        self.schema = schema
        
        # Initialize agents
        self.planner = PlannerAgent()
        self.sql_agent = SQLAgent()
        self.data_agent = DataAgent()
        self.analysis_agent = AnalysisAgent()
        self.visualization_agent = VisualizationAgent()
        
        # Initialize vector store for RAG
        self.vector_store = VectorStore(store_type=settings.vector_store_type)
        self.vector_store.load_schema(schema)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("planner", self._plan_node)
        workflow.add_node("sql_generator", self._sql_node)
        workflow.add_node("data_retriever", self._data_node)
        workflow.add_node("analyzer", self._analysis_node)
        workflow.add_node("visualizer", self._visualization_node)
        
        # Set entry point
        workflow.set_entry_point("planner")
        
        # Add edges
        workflow.add_edge("planner", "sql_generator")
        workflow.add_edge("sql_generator", "data_retriever")
        workflow.add_conditional_edges(
            "data_retriever",
            self._route_after_data,
            {
                "analyze": "analyzer",
                "visualize": "visualizer",
                "end": END
            }
        )
        workflow.add_conditional_edges(
            "analyzer",
            self._route_after_analysis,
            {
                "visualize": "visualizer",
                "end": END
            }
        )
        workflow.add_edge("visualizer", END)
        
        return workflow.compile()
    
    def _plan_node(self, state: AgentState) -> Dict[str, Any]:
        """Planning node."""
        result = self.planner.execute(state["question"], {})
        
        return {
            "plan": result.get("plan", []),
            "messages": [f"Plan created: {result.get('plan_text', '')}"]
        }
    
    def _sql_node(self, state: AgentState) -> Dict[str, Any]:
        """SQL generation node."""
        # Enhance schema with RAG
        relevant_schema = self._get_relevant_schema(state["question"])
        
        result = self.sql_agent.execute(
            state["question"],
            {"schema": relevant_schema}
        )
        
        sql_query = result.get("sql_query", "")
        return {
            "sql_query": sql_query,
            "messages": [f"Generated SQL: {sql_query}"]
        }
    
    def _data_node(self, state: AgentState) -> Dict[str, Any]:
        """Data retrieval node."""
        result = self.data_agent.execute(
            state["sql_query"],
            {"database_path": self.database_path}
        )
        
        if result.get("success"):
            data = result.get("data")
            return {
                "data": data,
                "messages": [f"Retrieved {result.get('rows', 0)} rows"]
            }
        else:
            return {
                "messages": [f"Data retrieval failed: {result.get('error', 'Unknown error')}"],
                "final_response": f"Error: {result.get('error', 'Failed to retrieve data')}"
            }
    
    def _analysis_node(self, state: AgentState) -> Dict[str, Any]:
        """Analysis node."""
        result = self.analysis_agent.execute(
            state["question"],
            {"data": state["data"]}
        )
        
        if result.get("success"):
            return {
                "analysis": result.get("analysis", ""),
                "messages": [f"Analysis completed"]
            }
        else:
            return {
                "messages": [f"Analysis failed: {result.get('error', 'Unknown error')}"]
            }
    
    def _visualization_node(self, state: AgentState) -> Dict[str, Any]:
        """Visualization node."""
        result = self.visualization_agent.execute(
            state["question"],
            {"data": state["data"]}
        )
        
        if result.get("success"):
            return {
                "figure": result.get("figure"),
                "messages": [f"Visualization created"],
                "final_response": state.get("analysis", "Data visualization created")
            }
        else:
            return {
                "messages": [f"Visualization failed: {result.get('error', 'Unknown error')}"],
                "final_response": state.get("analysis", "Analysis completed without visualization")
            }
    
    def _route_after_data(self, state: AgentState) -> str:
        """Route after data retrieval based on plan."""
        plan = state.get("plan", [])
        
        # Check if we need analysis
        needs_analysis = any(step.get("agent") == "analysis" for step in plan)
        needs_viz = any(step.get("agent") == "visualization" for step in plan)
        
        if needs_analysis:
            return "analyze"
        elif needs_viz:
            return "visualize"
        else:
            return "end"
    
    def _route_after_analysis(self, state: AgentState) -> str:
        """Route after analysis based on plan."""
        plan = state.get("plan", [])
        needs_viz = any(step.get("agent") == "visualization" for step in plan)
        
        if needs_viz:
            return "visualize"
        else:
            # Set final response if not already set
            if not state.get("final_response"):
                state["final_response"] = state.get("analysis", "Analysis completed")
            return "end"
    
    def _get_relevant_schema(self, question: str) -> str:
        """Get relevant schema information using RAG.
        
        Args:
            question: User's question
            
        Returns:
            Relevant schema information
        """
        # Search for relevant schema parts
        results = self.vector_store.search(question, k=3)
        
        if results:
            relevant_schema = "\n\n".join([doc.get("text", "") for doc in results])
            return relevant_schema
        
        # Fallback to full schema
        return self.schema
    
    def run(self, question: str) -> Dict[str, Any]:
        """Run the orchestrator with a question.
        
        Args:
            question: Natural language question
            
        Returns:
            Dictionary with results including analysis, figure, etc.
        """
        initial_state = {
            "question": question,
            "plan": [],
            "current_step": 0,
            "schema": self.schema,
            "database_path": self.database_path,
            "sql_query": "",
            "data": None,
            "analysis": "",
            "figure": None,
            "messages": [],
            "final_response": ""
        }
        
        # Run the workflow
        final_state = self.workflow.invoke(initial_state)
        
        return {
            "question": question,
            "sql_query": final_state.get("sql_query", ""),
            "data": final_state.get("data"),
            "analysis": final_state.get("analysis", ""),
            "figure": final_state.get("figure"),
            "messages": final_state.get("messages", []),
            "final_response": final_state.get("final_response", ""),
        }
