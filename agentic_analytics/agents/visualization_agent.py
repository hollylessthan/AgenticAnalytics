"""Visualization agent."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Any, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from agentic_analytics.agents.base import BaseAgent


class VisualizationAgent(BaseAgent):
    """Agent responsible for creating visualizations."""
    
    def __init__(self):
        super().__init__(
            name="Visualization Agent",
            description="Creates charts and visualizations from data"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert data visualization specialist.
            Given a dataset and a request, determine the best visualization type.
            
            Dataset columns: {columns}
            Dataset shape: {shape}
            
            Available chart types:
            - line: For time series or continuous data
            - bar: For categorical comparisons
            - scatter: For relationship between two variables
            - histogram: For distribution of a single variable
            - box: For distribution and outliers
            - pie: For composition/proportions
            
            Respond with a JSON object with this structure:
            {{
                "chart_type": "bar",
                "x_column": "column_name",
                "y_column": "column_name",
                "title": "Chart Title",
                "color": "optional_column_for_color"
            }}
            """),
            ("user", "{request}")
        ])
    
    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create visualization from data.
        
        Args:
            task: Visualization request
            context: Dictionary containing 'data' (pandas DataFrame)
            
        Returns:
            Dictionary with 'figure' (plotly figure) and 'success' status
        """
        try:
            df = context.get("data")
            if df is None or not isinstance(df, pd.DataFrame):
                return {
                    "success": False,
                    "error": "No valid data provided for visualization",
                    "agent": self.name
                }
            
            # Get visualization specification from LLM
            messages = self.prompt.format_messages(
                columns=", ".join(df.columns),
                shape=f"{df.shape[0]} rows x {df.shape[1]} columns",
                request=task
            )
            
            response = self.llm.invoke(messages)
            
            # Parse the response to get visualization config
            # For simplicity, we'll use a heuristic approach
            fig = self._create_smart_visualization(df, task)
            
            return {
                "success": True,
                "figure": fig,
                "agent": self.name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
    
    def _create_smart_visualization(self, df: pd.DataFrame, request: str) -> go.Figure:
        """Create an appropriate visualization based on data characteristics.
        
        Args:
            df: DataFrame to visualize
            request: User's visualization request
            
        Returns:
            Plotly figure
        """
        request_lower = request.lower()
        
        # Detect chart type from request
        if "line" in request_lower or "trend" in request_lower or "time" in request_lower:
            return self._create_line_chart(df)
        elif "scatter" in request_lower or "correlation" in request_lower:
            return self._create_scatter_plot(df)
        elif "histogram" in request_lower or "distribution" in request_lower:
            return self._create_histogram(df)
        elif "pie" in request_lower or "proportion" in request_lower:
            return self._create_pie_chart(df)
        else:
            # Default to bar chart
            return self._create_bar_chart(df)
    
    def _create_bar_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create a bar chart."""
        # Try to find appropriate columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(exclude=['number']).columns
        
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]
            fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
        elif len(numeric_cols) >= 2:
            fig = px.bar(df, x=df.index, y=numeric_cols[0], title=f"{numeric_cols[0]} Distribution")
        else:
            # Fallback: just show the first column
            fig = px.bar(df, y=df.columns[0], title=f"{df.columns[0]} Values")
        
        return fig
    
    def _create_line_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create a line chart."""
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) > 0:
            fig = px.line(df, y=numeric_cols[0], title=f"{numeric_cols[0]} Trend")
        else:
            fig = px.line(df, y=df.columns[0], title="Data Trend")
        
        return fig
    
    def _create_scatter_plot(self, df: pd.DataFrame) -> go.Figure:
        """Create a scatter plot."""
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) >= 2:
            fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], 
                           title=f"{numeric_cols[1]} vs {numeric_cols[0]}")
        else:
            fig = px.scatter(df, y=df.columns[0], title="Data Scatter")
        
        return fig
    
    def _create_histogram(self, df: pd.DataFrame) -> go.Figure:
        """Create a histogram."""
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) > 0:
            fig = px.histogram(df, x=numeric_cols[0], title=f"{numeric_cols[0]} Distribution")
        else:
            fig = px.histogram(df, x=df.columns[0], title="Data Distribution")
        
        return fig
    
    def _create_pie_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create a pie chart."""
        # Get first two columns for pie chart
        if len(df.columns) >= 2:
            fig = px.pie(df, names=df.columns[0], values=df.columns[1], 
                        title=f"{df.columns[1]} by {df.columns[0]}")
        else:
            # Count occurrences
            value_counts = df[df.columns[0]].value_counts()
            fig = px.pie(values=value_counts.values, names=value_counts.index,
                        title=f"{df.columns[0]} Distribution")
        
        return fig
