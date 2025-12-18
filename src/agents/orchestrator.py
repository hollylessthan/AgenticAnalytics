"""Agent orchestrator using LangGraph with hybrid routing."""

import time
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

from src.agents.base import AgentState
from src.agents.sql_agent import SQLAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.visualization_agent import VisualizationAgent
from src.agents.communication_agent import CommunicationAgent
from src.agents.query_classifier import QueryClassifier, PlanType
from src.config import Config
from src.utils.llm_factory import get_llm


class AgentOrchestrator:
    """Orchestrates multiple agents using LangGraph with hybrid routing."""
    
    def __init__(self, config: Config = None, smart_limit: bool = True, smart_limit_rows: int = 1000, status_callback=None):
        """Initialize the orchestrator.
        
        Args:
            config: Configuration object (creates default if None)
            smart_limit: If True, automatically add LIMIT to SQL queries
            smart_limit_rows: Default LIMIT value
            status_callback: Optional callback function(agent_name: str, message: str, status: str)
        """
        self.config = config or Config()
        self.smart_limit = smart_limit
        self.smart_limit_rows = smart_limit_rows
        self.status_callback = status_callback
        
        # Initialize hybrid query classifier
        self.classifier = QueryClassifier(self.config)
        
        # Initialize agents
        self.sql_agent = SQLAgent(self.config, smart_limit=smart_limit, smart_limit_rows=smart_limit_rows)
        self.analysis_agent = AnalysisAgent(self.config)
        self.visualization_agent = VisualizationAgent(self.config)
        self.communication_agent = CommunicationAgent(self.config)
        
        # Metrics tracking
        self.metrics = {
            'tier1_count': 0,
            'tier2_count': 0,
            'tier3_count': 0,
            'agent_latencies': {}
        }
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the agent workflow graph with hybrid routing.
        
        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("classifier", self._classify_query)
        workflow.add_node("sql_agent", self._execute_sql_agent)
        workflow.add_node("analysis_agent", self._execute_analysis_agent)
        workflow.add_node("visualization_agent", self._execute_visualization_agent)
        workflow.add_node("communication_agent", self._execute_communication_agent)
        
        # Set entry point
        workflow.set_entry_point("classifier")
        
        # Add conditional edges based on plan_type
        workflow.add_conditional_edges(
            "classifier",
            self._route_from_classifier,
            {
                "sql_agent": "sql_agent",
                "visualization_agent": "visualization_agent",
                "analysis_agent": "analysis_agent",
                "communication_agent": "communication_agent"
            }
        )
        
        workflow.add_conditional_edges(
            "sql_agent",
            self._route_from_sql,
            {
                "analysis_agent": "analysis_agent",
                "visualization_agent": "visualization_agent",
                "communication_agent": "communication_agent"
            }
        )
        
        workflow.add_conditional_edges(
            "analysis_agent",
            self._route_from_analysis,
            {
                "visualization_agent": "visualization_agent",
                "communication_agent": "communication_agent"
            }
        )
        
        workflow.add_edge("visualization_agent", "communication_agent")
        workflow.add_edge("communication_agent", END)
        
        return workflow.compile()
    
    def _classify_query(self, state: AgentState) -> AgentState:
        """Classify query using hybrid 3-tier approach with context awareness.
        
        Args:
            state: Current state
            
        Returns:
            Updated state with plan_type, confidence_score, and context flags
        """
        if self.status_callback:
            self.status_callback("classifier", "🔍 Analyzing query type...", "running")
        
        start_time = time.time()
        
        # Check for snapshot references (e.g., "use data from step 2", "original data")
        has_reference, snapshot_id = self.classifier.extract_snapshot_reference(state.query)
        if has_reference and state.state_history:
            snapshot = state.get_snapshot(snapshot_id)
            if snapshot and snapshot.dataframe is not None:
                # Load data from referenced snapshot
                state.cached_dataframe = snapshot.dataframe
                state.last_sql_query = snapshot.sql_query
                state.referenced_snapshot_id = snapshot_id
                print(f"[Orchestrator] 📸 Using data from snapshot #{snapshot_id}: {snapshot.query[:60]}...")
        
        # Check if we have cached data
        has_cached_data = state.cached_dataframe is not None
        
        # Use hybrid classifier with context awareness
        plan_type, confidence, context_flags = self.classifier.classify_query(
            state.query, 
            has_cached_data=has_cached_data
        )
        
        # Update state
        state.plan_type = plan_type.value
        state.confidence_score = confidence
        state.reuse_data = context_flags['reuse_data']
        state.update_visualization = context_flags['update_viz']
        state.agent_chain.append("classifier")
        
        # Track which tier was used (approximate based on confidence)
        if confidence == 1.0:
            self.metrics['tier1_count'] += 1
            state.metadata['routing_tier'] = 'T1_regex'
        elif confidence >= 0.85:
            self.metrics['tier2_count'] += 1
            state.metadata['routing_tier'] = 'T2_keyword'
        else:
            self.metrics['tier3_count'] += 1
            state.metadata['routing_tier'] = 'T3_llm'
        
        elapsed = time.time() - start_time
        self.metrics['agent_latencies']['classifier'] = elapsed
        
        context_info = []
        if context_flags['reuse_data']:
            context_info.append("reuse_data")
        if context_flags['update_viz']:
            context_info.append("update_viz")
        
        if self.status_callback:
            plan_msg = f"✓ Plan: {state.plan_type} (confidence: {state.confidence_score:.0%})"
            self.status_callback("classifier", plan_msg, "complete")
        
        context_str = f", Context: {', '.join(context_info)}" if context_info else ""
        print(f"[Classifier] Plan: {plan_type.value}, Confidence: {confidence:.2f}, "
              f"Tier: {state.metadata['routing_tier']}{context_str}, Time: {elapsed*1000:.1f}ms")
        
        return state
    
    def _route_from_classifier(self, state: AgentState) -> str:
        """Route from classifier based on plan_type and context.
        
        Args:
            state: Current state
            
        Returns:
            Next node name
        """
        # If reusing data, skip SQL agent
        if state.reuse_data and state.cached_dataframe is not None:
            print("[Orchestrator] Reusing cached data, skipping SQL agent")
            
            # Restore cached data to query_results
            state.query_results = state.cached_dataframe
            state.sql_query = state.last_sql_query
            
            # Check if query asks for data transformation (convert, format, etc.)
            query_lower = state.query.lower()
            needs_transformation = any(keyword in query_lower for keyword in ['convert', 'format', 'transform', 'change to', 'update the'])
            
            # If asking for data transformation, need to run SQL agent
            if needs_transformation:
                print("[Orchestrator] Data transformation requested, running SQL agent")
                return "sql_agent"
            
            # Route based on what user wants to do with the data
            if state.update_visualization or state.plan_type == PlanType.SQL_VIZ.value:
                return "visualization_agent"
            elif state.plan_type == PlanType.SQL_ANALYSIS.value or state.plan_type == PlanType.SQL_ANALYSIS_VIZ.value:
                return "analysis_agent"
            else:
                # For explanation questions, go directly to communication agent
                return "communication_agent"
        
        # Normal flow: start with SQL agent
        return "sql_agent"
    
    def _execute_sql_agent(self, state: AgentState) -> AgentState:
        """Execute SQL agent with timing."""
        if self.status_callback:
            self.status_callback("sql_agent", "💾 Generating and executing SQL query...", "running")
        
        start_time = time.time()
        state = self.sql_agent.execute(state)
        elapsed = time.time() - start_time
        self.metrics['agent_latencies']['sql_agent'] = elapsed
        print(f"[SQL Agent] Time: {elapsed*1000:.1f}ms")
        
        if self.status_callback:
            if state.query_results is not None:
                import pandas as pd
                if isinstance(state.query_results, pd.DataFrame):
                    row_count = len(state.query_results)
                    self.status_callback("sql_agent", f"✓ Retrieved {row_count:,} rows", "complete")
                else:
                    self.status_callback("sql_agent", "✓ Query executed", "complete")
            else:
                self.status_callback("sql_agent", "✓ Query completed", "complete")
        
        return state
    
    def _execute_analysis_agent(self, state: AgentState) -> AgentState:
        """Execute analysis agent with timing."""
        if self.status_callback:
            self.status_callback("analysis_agent", "📊 Running statistical analysis...", "running")
        
        start_time = time.time()
        state = self.analysis_agent.execute(state)
        elapsed = time.time() - start_time
        self.metrics['agent_latencies']['analysis_agent'] = elapsed
        print(f"[Analysis Agent] Time: {elapsed*1000:.1f}ms")
        
        if self.status_callback:
            self.status_callback("analysis_agent", "✓ Analysis complete", "complete")
        
        return state
    
    def _execute_visualization_agent(self, state: AgentState) -> AgentState:
        """Execute visualization agent with timing."""
        if self.status_callback:
            self.status_callback("visualization_agent", "📈 Creating visualization...", "running")
        
        start_time = time.time()
        state = self.visualization_agent.execute(state)
        elapsed = time.time() - start_time
        self.metrics['agent_latencies']['visualization_agent'] = elapsed
        print(f"[Visualization Agent] Time: {elapsed*1000:.1f}ms")
        
        if self.status_callback:
            self.status_callback("visualization_agent", "✓ Chart generated", "complete")
        
        return state
    
    def _execute_communication_agent(self, state: AgentState) -> AgentState:
        """Execute communication agent with timing."""
        if self.status_callback:
            self.status_callback("communication_agent", "💬 Preparing response...", "running")
        
        start_time = time.time()
        state = self.communication_agent.execute(state)
        elapsed = time.time() - start_time
        self.metrics['agent_latencies']['communication_agent'] = elapsed
        print(f"[Communication Agent] Time: {elapsed*1000:.1f}ms")
        
        if self.status_callback:
            self.status_callback("communication_agent", "✓ Response ready", "complete")
        
        return state
    
    def _route_from_sql(self, state: AgentState) -> str:
        """Route from SQL agent based on plan_type.
        
        Args:
            state: Current state
            
        Returns:
            Next node name
        """
        # If errors occurred, go straight to communication
        if state.errors:
            return "communication_agent"
        
        # Route based on classified plan type
        if state.plan_type == PlanType.SQL_ONLY.value:
            return "communication_agent"
        elif state.plan_type == PlanType.SQL_ANALYSIS.value:
            return "analysis_agent"
        elif state.plan_type == PlanType.SQL_VIZ.value:
            return "visualization_agent"
        elif state.plan_type == PlanType.SQL_ANALYSIS_VIZ.value:
            return "analysis_agent"  # Analysis first, then viz
        else:
            return "communication_agent"
    
    def _route_from_analysis(self, state: AgentState) -> str:
        """Route from analysis agent based on plan_type.
        
        Args:
            state: Current state
            
        Returns:
            Next node name
        """
        # If errors occurred, go straight to communication
        if state.errors:
            return "communication_agent"
        
        # If plan includes visualization, route there
        if state.plan_type == PlanType.SQL_ANALYSIS_VIZ.value:
            return "visualization_agent"
        else:
            return "communication_agent"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get routing and performance metrics.
        
        Returns:
            Dictionary with metrics
        """
        total_queries = sum([
            self.metrics['tier1_count'],
            self.metrics['tier2_count'],
            self.metrics['tier3_count']
        ])
        
        if total_queries == 0:
            return self.metrics
        
        return {
            **self.metrics,
            'tier_percentages': {
                'tier1': (self.metrics['tier1_count'] / total_queries) * 100,
                'tier2': (self.metrics['tier2_count'] / total_queries) * 100,
                'tier3': (self.metrics['tier3_count'] / total_queries) * 100,
            },
            'total_queries': total_queries
        }
    
    def run(self, user_query: str, conversation_history: list = None, previous_state: AgentState = None) -> AgentState:
        """Run the orchestrator with a user query, optionally maintaining session state.
        
        Args:
            user_query: User's natural language query
            conversation_history: Previous conversation messages
            previous_state: Previous AgentState to maintain cached data (optional)
            
        Returns:
            Final agent state
        """
        start_time = time.time()
        
        # Create initial state, optionally inheriting cached data from previous state
        initial_state = AgentState(
            query=user_query,
            user_query=user_query,  # Backward compatibility
            conversation_history=conversation_history or []
        )
        
        # Inherit session state from previous query if provided
        if previous_state:
            initial_state.cached_dataframe = previous_state.cached_dataframe
            initial_state.last_sql_query = previous_state.last_sql_query
            initial_state.current_visualization_code = previous_state.current_visualization_code
            print(f"[Orchestrator] Inherited session state from previous query")
        
        final_state = self.graph.invoke(initial_state)
        
        # Convert dict to AgentState if needed (LangGraph returns dict)
        if isinstance(final_state, dict):
            final_state = AgentState(**final_state)
        
        total_time = time.time() - start_time
        print(f"\n[Orchestrator] Total execution time: {total_time*1000:.1f}ms")
        print(f"[Orchestrator] Agent chain: {' -> '.join(final_state.agent_chain)}")
        
        return final_state
