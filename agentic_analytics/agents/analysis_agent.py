"""Python analysis agent."""

import pandas as pd
from typing import Any, Dict
from langchain_core.prompts import ChatPromptTemplate
from agentic_analytics.agents.base import BaseAgent


class AnalysisAgent(BaseAgent):
    """Agent responsible for analyzing data using Python."""
    
    def __init__(self):
        super().__init__(
            name="Analysis Agent",
            description="Performs statistical analysis and data transformations using Python"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert data analyst. 
            Given a dataset and a question, provide a clear analysis.
            
            Dataset Summary:
            {data_summary}
            
            Instructions:
            - Provide insights based on the data
            - Use statistical measures when appropriate
            - Be clear and concise
            - Highlight key findings
            """),
            ("user", "{question}")
        ])
    
    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data and provide insights.
        
        Args:
            task: Analysis question or request
            context: Dictionary containing 'data' (pandas DataFrame)
            
        Returns:
            Dictionary with 'analysis' text and 'success' status
        """
        try:
            df = context.get("data")
            if df is None or not isinstance(df, pd.DataFrame):
                return {
                    "success": False,
                    "error": "No valid data provided for analysis",
                    "agent": self.name
                }
            
            # Create data summary
            data_summary = self._create_summary(df)
            
            messages = self.prompt.format_messages(
                data_summary=data_summary,
                question=task
            )
            
            response = self.llm.invoke(messages)
            analysis = response.content.strip()
            
            # Compute basic statistics
            stats = self._compute_statistics(df)
            
            return {
                "success": True,
                "analysis": analysis,
                "statistics": stats,
                "agent": self.name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
    
    def _create_summary(self, df: pd.DataFrame) -> str:
        """Create a summary of the dataframe."""
        summary_parts = [
            f"Shape: {df.shape[0]} rows, {df.shape[1]} columns",
            f"Columns: {', '.join(df.columns)}",
            f"\nFirst few rows:\n{df.head().to_string()}",
        ]
        
        # Add numeric column statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary_parts.append(f"\nNumeric statistics:\n{df[numeric_cols].describe().to_string()}")
        
        return "\n".join(summary_parts)
    
    def _compute_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute basic statistics for the dataframe."""
        stats = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
        }
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            stats["numeric_summary"] = df[numeric_cols].describe().to_dict()
        
        return stats
