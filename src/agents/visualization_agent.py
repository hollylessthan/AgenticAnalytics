"""Visualization Agent for creating data visualizations."""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel

from .base import BaseAgent, AgentState


class VisualizationAgent(BaseAgent):
    """Agent that creates data visualizations."""
    
    def __init__(self, llm: BaseChatModel):
        """Initialize Visualization Agent.
        
        Args:
            llm: Language model instance
        """
        super().__init__(
            name="visualization_agent",
            description="Creates charts and visualizations from data"
        )
        self.llm = llm
        self.output_dir = "outputs/visualizations"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def execute(self, state: AgentState) -> AgentState:
        """Execute visualization creation.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with visualization path
        """
        try:
            # Prepare data
            if state.query_results is not None:
                df = self._prepare_dataframe(state.query_results)
            else:
                state.errors.append("No data available for visualization")
                return state
            
            # Generate visualization code
            viz_code = self._generate_visualization_code(state.user_query, df)
            state.visualization_code = viz_code
            
            # Execute visualization
            viz_path = self._execute_visualization(viz_code, df)
            state.visualization_path = viz_path
            
            state.next_agent = None  # Visualization is typically the last step
            
        except Exception as e:
            state.errors.append(f"Visualization Agent Error: {str(e)}")
            state.next_agent = None
        
        return state
    
    def _prepare_dataframe(self, data) -> pd.DataFrame:
        """Convert query results to DataFrame.
        
        Args:
            data: Query results
            
        Returns:
            pandas DataFrame
        """
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, list):
            return pd.DataFrame(data)
        else:
            return pd.DataFrame([data])
    
    def _generate_visualization_code(self, user_query: str, df: pd.DataFrame) -> str:
        """Generate visualization code.
        
        Args:
            user_query: User's query
            df: DataFrame to visualize
            
        Returns:
            Python code string
        """
        df_info = f"Shape: {df.shape}\nColumns: {list(df.columns)}\nDtypes:\n{df.dtypes.to_dict()}"
        sample_data = df.head().to_dict()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert data visualization specialist. Generate Python code to create a visualization.

DataFrame Information:
{df_info}

Sample Data:
{sample_data}

Requirements:
- Use matplotlib and/or seaborn
- Create a figure using plt.figure()
- Choose appropriate visualization type (bar, line, scatter, heatmap, etc.)
- Add proper labels, title, and legend
- Use plt.tight_layout() for better spacing
- DO NOT include plt.show() or plt.savefig()
- Assume df, plt, sns are already imported and available
- Make it visually appealing with good color schemes

The code should create a complete visualization ready to be saved."""),
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
    
    def _execute_visualization(self, code: str, df: pd.DataFrame) -> str:
        """Execute visualization code and save figure.
        
        Args:
            code: Python code to execute
            df: DataFrame to visualize
            
        Returns:
            Path to saved visualization
        """
        # Create safe execution environment
        local_vars = {
            'df': df,
            'plt': plt,
            'sns': sns,
            'pd': pd
        }
        
        try:
            # Execute the code
            exec(code, {"__builtins__": __builtins__}, local_vars)
            
            # Save the figure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"viz_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            plt.close()
            raise Exception(f"Visualization execution failed: {str(e)}")
