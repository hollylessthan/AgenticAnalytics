"""Analysis Agent for performing Python data analysis."""

import pandas as pd
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel

from .base import BaseAgent, AgentState


class AnalysisAgent(BaseAgent):
    """Agent that performs data analysis using Python."""
    
    def __init__(self, llm: BaseChatModel):
        """Initialize Analysis Agent.
        
        Args:
            llm: Language model instance
        """
        super().__init__(
            name="analysis_agent",
            description="Performs statistical and analytical operations on data"
        )
        self.llm = llm
    
    def execute(self, state: AgentState) -> AgentState:
        """Execute data analysis.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with analysis results
        """
        try:
            # Convert query results to DataFrame if needed
            if state.query_results is not None:
                df = self._prepare_dataframe(state.query_results)
            else:
                state.errors.append("No data available for analysis")
                return state
            
            # Generate analysis code
            analysis_code = self._generate_analysis_code(state.user_query, df)
            state.analysis_code = analysis_code
            
            # Execute analysis
            analysis_results = self._execute_analysis(analysis_code, df)
            state.analysis_results = analysis_results
            
            # Determine next step
            state.next_agent = self._determine_next_step(state.user_query)
            
        except Exception as e:
            state.errors.append(f"Analysis Agent Error: {str(e)}")
            state.next_agent = None
        
        return state
    
    def _prepare_dataframe(self, data: Any) -> pd.DataFrame:
        """Convert query results to DataFrame.
        
        Args:
            data: Query results (list of dicts, tuples, etc.)
            
        Returns:
            pandas DataFrame
        """
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, list):
            return pd.DataFrame(data)
        else:
            return pd.DataFrame([data])
    
    def _generate_analysis_code(self, user_query: str, df: pd.DataFrame) -> str:
        """Generate Python analysis code.
        
        Args:
            user_query: User's query
            df: DataFrame to analyze
            
        Returns:
            Python code string
        """
        # Get DataFrame info
        df_info = f"Shape: {df.shape}\nColumns: {list(df.columns)}\nDtypes:\n{df.dtypes.to_dict()}"
        sample_data = df.head().to_dict()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert data analyst. Generate Python code to analyze the given DataFrame.

DataFrame Information:
{df_info}

Sample Data:
{sample_data}

Requirements:
- Use pandas and numpy for analysis
- Store results in a dictionary called 'results'
- Include descriptive statistics, correlations, or other relevant analysis
- Code should be safe and efficient
- Don't include import statements or DataFrame creation
- Assume df variable is already available

Example:
results = {{
    'mean': df['column'].mean(),
    'correlation': df.corr().to_dict(),
    'summary': df.describe().to_dict()
}}"""),
            ("user", "{question}")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            df_info=df_info,
            sample_data=str(sample_data)[:500],
            question=user_query
        ))
        
        # Clean up code
        code = response.content.strip()
        if code.startswith("```python"):
            code = code[9:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        
        return code.strip()
    
    def _execute_analysis(self, code: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute analysis code safely.
        
        Args:
            code: Python code to execute
            df: DataFrame to analyze
            
        Returns:
            Analysis results dictionary
        """
        import numpy as np
        
        # Create safe execution environment
        local_vars = {
            'df': df,
            'pd': pd,
            'np': np,
            'results': {}
        }
        
        try:
            exec(code, {"__builtins__": __builtins__}, local_vars)
            return local_vars.get('results', {})
        except Exception as e:
            return {'error': str(e), 'code': code}
    
    def _determine_next_step(self, user_query: str) -> Optional[str]:
        """Determine what agent should run next.
        
        Args:
            user_query: User's query
            
        Returns:
            Next agent name or None
        """
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ["plot", "chart", "visualize", "graph", "show"]):
            return "visualization"
        else:
            return None
