"""Planning and coordination agent."""

from typing import Any, Dict, List
from langchain_core.prompts import ChatPromptTemplate
from agentic_analytics.agents.base import BaseAgent


class PlannerAgent(BaseAgent):
    """Agent responsible for planning and coordinating task execution."""
    
    def __init__(self):
        super().__init__(
            name="Planner Agent",
            description="Plans and coordinates the execution of data analysis tasks"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert task planner for data analysis.
            Given a user question, determine the sequence of steps needed to answer it.
            
            Available agents:
            1. SQL Agent - Converts natural language to SQL queries
            2. Data Agent - Executes SQL queries and retrieves data
            3. Analysis Agent - Performs statistical analysis on data
            4. Visualization Agent - Creates charts and visualizations
            
            Instructions:
            - Break down the user's request into a sequence of steps
            - Each step should specify which agent to use
            - Steps should be in logical order
            - Output a clear plan as a numbered list
            
            Example format:
            1. Use SQL Agent to convert the question into a SQL query
            2. Use Data Agent to execute the query and retrieve data
            3. Use Analysis Agent to analyze the results
            4. Use Visualization Agent to create a chart (if visualization is requested)
            """),
            ("user", "{question}")
        ])
    
    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create an execution plan for the user's question.
        
        Args:
            task: User's question or request
            context: Additional context (not used for planning)
            
        Returns:
            Dictionary with 'plan' (list of steps) and 'success' status
        """
        try:
            messages = self.prompt.format_messages(question=task)
            response = self.llm.invoke(messages)
            plan_text = response.content.strip()
            
            # Parse the plan into steps
            steps = self._parse_plan(plan_text, task)
            
            return {
                "success": True,
                "plan": steps,
                "plan_text": plan_text,
                "agent": self.name
            }
        except Exception as e:
            # Fallback to default plan if LLM fails
            steps = self._create_default_plan(task)
            return {
                "success": True,
                "plan": steps,
                "plan_text": "Using default plan",
                "agent": self.name,
                "note": f"LLM planning failed: {str(e)}, using default plan"
            }
    
    def _parse_plan(self, plan_text: str, question: str) -> List[Dict[str, Any]]:
        """Parse plan text into structured steps."""
        steps = []
        
        # Determine what agents are needed based on keywords
        needs_sql = True  # Almost always need SQL
        needs_data = True  # Always need data retrieval
        needs_analysis = any(word in question.lower() for word in 
                            ["analyze", "analysis", "insight", "summary", "statistics", "compare"])
        needs_viz = any(word in question.lower() for word in 
                       ["chart", "plot", "graph", "visualize", "visualization", "show"])
        
        if needs_sql:
            steps.append({
                "agent": "sql",
                "description": "Generate SQL query from natural language question"
            })
        
        if needs_data:
            steps.append({
                "agent": "data",
                "description": "Execute SQL query and retrieve data"
            })
        
        if needs_analysis:
            steps.append({
                "agent": "analysis",
                "description": "Analyze the retrieved data"
            })
        
        if needs_viz:
            steps.append({
                "agent": "visualization",
                "description": "Create visualization of the data"
            })
        
        # If no specific analysis or visualization is requested, add analysis by default
        if not needs_analysis and not needs_viz:
            steps.append({
                "agent": "analysis",
                "description": "Provide summary of the data"
            })
        
        return steps
    
    def _create_default_plan(self, question: str) -> List[Dict[str, Any]]:
        """Create a default plan when LLM planning fails."""
        return self._parse_plan("", question)
