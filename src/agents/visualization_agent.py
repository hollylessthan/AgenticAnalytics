"""Visualization Agent for creating data visualizations."""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import traceback
from typing import Optional
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate

from src.agents.base import BaseAgent, AgentState
from src.config import Config
from src.utils.llm_factory import get_llm


class VisualizationAgent(BaseAgent):
    """Agent that creates data visualizations."""
    
    def __init__(self, config: Config):
        """Initialize Visualization Agent.
        
        Args:
            config: Configuration object
        """
        super().__init__(
            config=config,
            name="visualization_agent",
            description="Creates charts and visualizations from data"
        )
        self.llm = get_llm()
        self.output_dir = "outputs/visualizations"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def execute(self, state: AgentState) -> AgentState:
        """Execute visualization creation.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with visualization path
        """
        # Use retry wrapper for execution
        return self.execute_with_retry(state, self._execute_impl)
    
    def _execute_impl(self, state: AgentState) -> AgentState:
        """Implementation of visualization execution (wrapped in retry logic)."""
        try:
            # Add to agent chain
            state.agent_chain.append("visualization_agent")
            
            # Check for data - try query_results first, then cached_dataframe
            data_source = None
            if state.query_results is not None:
                data_source = state.query_results
            elif state.cached_dataframe is not None:
                data_source = state.cached_dataframe
                print("[Visualization Agent] Using cached_dataframe as data source")
            else:
                raise ValueError("No query results available. Did the SQL query execute successfully? Check the SQL agent output.")
            
            # Prepare data
            df = self._prepare_dataframe(data_source)
            if df.empty:
                raise ValueError("Query returned no data. Cannot create visualization from empty dataset.")
            
            # Check if updating existing visualization
            if state.update_visualization and state.current_visualization_code:
                print(f"[Visualization Agent] Updating existing visualization")
                viz_code = self._update_visualization_code(
                    state.query, 
                    state.current_visualization_code,
                    df
                )
            else:
                # Generate and execute visualization code with error-aware retries
                max_viz_retries = 3
                viz_code = None
                viz_result = None
                
                for attempt in range(max_viz_retries):
                    if attempt == 0:
                        # First attempt: generate fresh code
                        viz_code = self._generate_visualization_code(state.query, df)
                    else:
                        # Subsequent attempts: regenerate based on error
                        error_info = viz_result.get('error', '')
                        error_trace = viz_result.get('traceback', '')
                        print(f"[Visualization Agent] Code failed: {error_info}")
                        print(f"[Visualization Agent] Regenerating code (attempt {attempt + 1}/{max_viz_retries})")
                        viz_code = self._regenerate_visualization_code(state.query, df, error_info, error_trace)
                    
                    # Execute the visualization code
                    viz_result = self._execute_visualization(viz_code, df)
                    
                    # Check if successful
                    if 'error' not in viz_result:
                        # Success!
                        print(f"[Visualization Agent] Successfully generated and executed visualization")
                        break
                    elif attempt == max_viz_retries - 1:
                        # Last attempt failed
                        raise Exception(f"Visualization code generation failed after {max_viz_retries} attempts: {viz_result['error']}")
                
                viz_path = viz_result.get('path') if 'error' not in viz_result else None
                state.visualization_path = viz_path
                state.visualization_paths.append(viz_path)
            
            state.visualization_code = viz_code
            
            # Cache the visualization code for potential updates
            state.current_visualization_code = viz_code
            
            action = "Updated" if state.update_visualization else "Created"
            print(f"[Visualization Agent] {action} visualization: {state.visualization_path}")
            
        except Exception as e:
            # Re-raise so retry logic can handle it
            raise
        
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
            ("system", """You are a data visualization specialist. Generate Python code to create effective visualizations.

Your ONLY job is to generate visualization code. Do NOT perform analysis or suggest insights.

DataFrame Information:
{df_info}

Sample Data (first few rows):
{sample_data}

Visualization Code Requirements:
1. Use matplotlib (plt) and/or seaborn (sns) - both available
2. Create figure: fig, ax = plt.subplots(figsize=(10, 6))
3. Choose appropriate chart type based on data:
   - Trends over time: Line chart (plt.plot or sns.lineplot)
   - Comparisons: Bar chart (plt.bar or sns.barplot)
   - Distributions: Histogram (plt.hist or sns.histplot)
   - Relationships: Scatter plot (plt.scatter or sns.scatterplot)
   - Correlations: Heatmap (sns.heatmap)
   - Categories: Pie chart (plt.pie) or bar chart
4. Add clear labels: ax.set_xlabel(), ax.set_ylabel(), ax.set_title()
5. Include legend if multiple series: ax.legend()
6. Use seaborn style for aesthetics: sns.set_style('whitegrid')
7. Apply tight_layout: plt.tight_layout()
8. DO NOT include plt.show() or plt.savefig() - these are handled separately
9. DO NOT include import statements
10. Assume df, plt, sns, pd are available
11. Handle missing values appropriately
12. Use color palettes for visual appeal: palette='viridis' or 'Set2'

Chart Type Selection Guide:
- "trend" / "over time" → Line chart
- "compare" / "by category" → Bar chart
- "distribution" / "frequency" → Histogram
- "correlation" / "relationship" → Scatter or heatmap
- "breakdown" / "proportion" → Pie chart

Example Structure:
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df['x'], df['y'])
ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
ax.set_title('Chart Title')
plt.tight_layout()"""),
            ("user", "Create visualization for: {question}")
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
    
    def _regenerate_visualization_code(self, user_query: str, df: pd.DataFrame, error_msg: str, error_trace: str) -> str:
        """Regenerate visualization code based on previous error.
        
        Args:
            user_query: User's visualization query
            df: DataFrame to visualize
            error_msg: Error message from failed execution
            error_trace: Full traceback from failed execution
            
        Returns:
            Corrected Python code string
        """
        df_info = f"Shape: {df.shape}\nColumns: {list(df.columns)}\nDtypes:\n{df.dtypes.to_dict()}"
        sample_data = df.head().to_dict()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data visualization specialist. Fix the Python code that previously failed.

DataFrame Information:
{df_info}

Sample Data (first few rows):
{sample_data}

PREVIOUS ERROR (fix this):
{error_trace}

Visualization Code Requirements:
1. Use matplotlib (plt) and seaborn (sns) - both available
2. Create figure: fig, ax = plt.subplots(figsize=(10, 6))
3. Choose appropriate chart type based on data
4. Add clear labels and title
5. DO NOT include import statements
6. Assume df, plt, sns, pd are available
7. FIX the previous error - analyze what went wrong and correct it
8. DO NOT include plt.show() or plt.savefig() - these are handled separately

Common Errors and Fixes:
- KeyError: Column doesn't exist → Check df.columns, use correct column names
- TypeError: Unsupported type → Check data types, convert if needed
- ValueError: Invalid parameter → Check parameter ranges
- AttributeError: No such method → Use correct method names
- IndexError: Out of bounds → Check array/list sizes

Output Format (complete, executable code):
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df['x'], df['y'])
ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
ax.set_title('Chart Title')
plt.tight_layout()"""),
            ("user", "Fix the visualization code for: {question}")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            df_info=df_info,
            sample_data=str(sample_data)[:500],
            error_trace=error_trace[:1000],  # Limit traceback size
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
    
    def _update_visualization_code(self, user_request: str, current_code: str, df: pd.DataFrame) -> str:
        """Update existing visualization code based on user request.
        
        Args:
            user_request: User's update request (e.g., "add x-axis label")
            current_code: Current visualization code
            df: DataFrame
            
        Returns:
            Updated Python code string
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are updating an existing visualization based on user feedback.

Current Visualization Code:
```python
{current_code}
```

User's Update Request: {request}

Generate the UPDATED complete visualization code incorporating the changes.

Rules:
1. Keep the same chart type unless explicitly asked to change
2. Preserve existing styling unless asked to change
3. Make ONLY the requested changes
4. Return complete executable code
5. NO markdown, NO explanations
6. Assume df, plt, sns, pd are available

Common updates:
- Labels: ax.set_xlabel(), ax.set_ylabel()
- Title: ax.set_title()
- Legend: ax.legend()
- Colors: color='red', palette='viridis'
- Size: figsize=(width, height)
- Chart type: Change plot type (bar → line, etc.)"""),
            ("user", "Update the visualization code")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            current_code=current_code,
            request=user_request
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
    
    def _execute_visualization(self, code: str, df: pd.DataFrame):
        """Execute visualization code and save figure.
        
        Args:
            code: Python code to execute
            df: DataFrame to visualize
            
        Returns:
            Dict with path (success) or error info (failure)
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
            
            return {'path': filepath}
            
        except Exception as e:
            plt.close()
            return {
                'error': str(e),
                'traceback': traceback.format_exc(),
                'code': code
            }
