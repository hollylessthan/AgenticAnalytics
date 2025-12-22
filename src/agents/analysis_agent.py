"""Analysis Agent for performing Python data analysis."""

import pandas as pd
import traceback
from typing import Dict, Any, Optional, List
from langchain_core.prompts import ChatPromptTemplate

from src.agents.base import BaseAgent, AgentState
from src.config import Config
from src.utils.llm_factory import get_llm


class AnalysisAgent(BaseAgent):
    """Agent that performs data analysis using Python."""
    
    def __init__(self, config: Config):
        """Initialize Analysis Agent.
        
        Args:
            config: Configuration object
        """
        super().__init__(
            config=config,
            name="analysis_agent",
            description="Performs statistical and analytical operations on data"
        )
        self.llm = get_llm()
        
        # Initialize RAG system for method selection
        try:
            from src.rag.rag_system import RAGSystem
            self.rag_system = RAGSystem(config)
            print("[AnalysisAgent] RAG system initialized for analysis method selection")
        except Exception as e:
            print(f"[AnalysisAgent] RAG system not available: {e}")
            self.rag_system = None
    
    def execute(self, state: AgentState) -> AgentState:
        """Execute data analysis.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with analysis results
        """
        # Use retry wrapper for execution
        return self.execute_with_retry(state, self._execute_impl)
    
    def _execute_impl(self, state: AgentState) -> AgentState:
        """Implementation of analysis execution (wrapped in retry logic)."""
        try:
            # Add to agent chain
            state.agent_chain.append("analysis_agent")
            
            # Get data source - prefer preprocessed data if available
            data_source = None
            if state.preprocessed_dataframe is not None:
                data_source = state.preprocessed_dataframe
                print("[AnalysisAgent] Using preprocessed dataframe")
            elif state.query_results is not None:
                data_source = state.query_results
            elif state.cached_dataframe is not None:
                data_source = state.cached_dataframe
                print("[AnalysisAgent] Using cached_dataframe as data source")
            else:
                raise ValueError("No data available for analysis")
            
            df = self._prepare_dataframe(data_source)
            
            if df.empty:
                raise ValueError("Query returned no rows for analysis")
            
            # Try to generate and execute analysis code with error-aware retries
            analysis_code = None
            analysis_results = None
            max_code_retries = 3
            
            # RAG-powered analysis method selection
            selected_methods = []
            if self.rag_system and state.data_profile:
                try:
                    selected_methods = self._rag_select_analysis_methods(state.query, state.data_profile, df)
                    if selected_methods:
                        print(f"[AnalysisAgent] RAG selected {len(selected_methods)} analysis methods")
                except Exception as e:
                    print(f"[AnalysisAgent] RAG method selection failed: {e}, using LLM fallback")
            
            for attempt in range(max_code_retries):
                if attempt == 0:
                    # First attempt: generate fresh code with RAG guidance
                    analysis_code = self._generate_analysis_code(
                        state.query, df, state, 
                        rag_methods=selected_methods
                    )
                else:
                    # Subsequent attempts: regenerate code based on previous error
                    error_info = analysis_results.get('error', '')
                    error_trace = analysis_results.get('traceback', '')
                    print(f"[Analysis Agent] Code failed with error: {error_info}")
                    print(f"[Analysis Agent] Regenerating code (attempt {attempt + 1}/{max_code_retries})")
                    analysis_code = self._regenerate_analysis_code(state.query, df, error_info, error_trace)
                
                # Execute the analysis code
                analysis_results = self._execute_analysis(analysis_code, df)
                state.analysis_code = analysis_code
                
                # Check if successful
                if 'error' not in analysis_results:
                    # Success!
                    state.analysis_results = self._format_results(analysis_results)
                    print(f"[Analysis Agent] Successfully generated and executed analysis code")
                    break
                elif attempt == max_code_retries - 1:
                    # Last attempt failed - raise the error
                    raise Exception(f"Analysis code generation failed after {max_code_retries} attempts: {analysis_results['error']}")
            
            print(f"[Analysis Agent] Completed analysis with {len(analysis_results)} results")
            
        except Exception as e:
            # Re-raise so retry logic can handle it
            raise
        
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
    
    def _generate_analysis_code(
        self, 
        user_query: str, 
        df: pd.DataFrame, 
        state: Optional[AgentState] = None,
        rag_methods: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generate Python analysis code with optional RAG method guidance.
        
        Args:
            user_query: User's query
            df: DataFrame to analyze
            state: Optional agent state with preprocessing info
            rag_methods: Optional RAG-selected method cards
            
        Returns:
            Python code string
        """
        # Get DataFrame info
        df_info = f"Shape: {df.shape}\nColumns: {list(df.columns)}\nDtypes:\n{df.dtypes.to_dict()}"
        sample_data = df.head().to_dict()
        
        # Get distribution info if available (from PreprocessingAgent)
        distribution_guidance = ""
        if state and state.preprocessing_needed:
            needs = state.preprocessing_needed.get("needs", {})
            recommended_corr = needs.get("recommended_correlation", "pearson")
            non_normal = needs.get("non_normal_features", [])
            
            if non_normal:
                distribution_guidance = f"""
IMPORTANT DISTRIBUTION NOTES:
- Non-normal features detected: {non_normal[:5]}
- Recommended correlation method: {recommended_corr}
- For correlation analysis, use: df.corr(method='{recommended_corr}')
- For statistical tests with non-normal data, use non-parametric alternatives
"""
        
        # Build RAG method guidance
        rag_guidance = ""
        if rag_methods:
            rag_guidance = "\nRECOMMENDED METHODS FROM RAG:\n"
            for method_info in rag_methods[:3]:  # Limit to top 3
                card = method_info.get('method_card')
                if card:
                    rag_guidance += f"\n{card.method_name}:\n"
                    rag_guidance += f"  Description: {card.when_to_use}\n"
                    rag_guidance += f"  Use case: {method_info.get('reasoning', '')}\n"
                    if card.code_example:
                        rag_guidance += f"  Example code:\n{card.code_example}\n"
                    rag_guidance += "\n"
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a statistical analysis specialist. Generate Python code to perform data analysis.

Your ONLY job is to generate analysis code. Do NOT create visualizations or suggest next steps.

DataFrame Information:
{df_info}

Sample Data (first few rows):
{sample_data}

{distribution_guidance}

{rag_guidance}

Analysis Code Requirements:
1. Use pandas (pd), numpy (np), scipy.stats, and statsmodels - all are available
2. Store ALL results in a dictionary named 'results'
3. Include descriptive labels for each result
4. Focus on statistical analysis appropriate for the query
5. DO NOT include import statements
6. DO NOT create plots or visualizations
7. Assume 'df' variable contains the data
8. Handle missing values gracefully
9. Convert numpy types to Python types for serialization
10. If RAG methods are provided above, USE THEM as guidance for your analysis

Common Analysis Patterns:
- Descriptive stats: results['summary'] = df.describe().to_dict()
- Aggregations: results['total'] = float(df['col'].sum())
- Correlations: results['correlation'] = df.corr(method='pearson').to_dict()  # or 'spearman' for non-normal
- Grouping: results['by_group'] = df.groupby('col')['val'].mean().to_dict()
- Trends: results['trend'] = df['col'].pct_change().mean()
- Distributions: results['percentiles'] = df['col'].quantile([0.25, 0.5, 0.75]).to_dict()
- Statistical Tests (from statsmodels/scipy): Use RAG-recommended methods when available

Output Format:
results = {{
    'metric_name': value,
    'another_metric': another_value
}}"""),
            ("user", "Analyze: {question}")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            df_info=df_info,
            sample_data=str(sample_data)[:500],
            distribution_guidance=distribution_guidance,
            rag_guidance=rag_guidance,
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
            Analysis results dictionary (or error dict if execution failed)
        """
        import numpy as np
        from scipy import stats
        
        # Create safe execution environment
        local_vars = {
            'df': df,
            'pd': pd,
            'np': np,
            'stats': stats,
            'results': {}
        }
        
        try:
            exec(code, {"__builtins__": __builtins__}, local_vars)
            return local_vars.get('results', {})
        except Exception as e:
            # Capture both error message and full traceback for regeneration
            return {
                'error': str(e),
                'traceback': traceback.format_exc(),
                'code': code
            }
    
    def _regenerate_analysis_code(self, user_query: str, df: pd.DataFrame, error_msg: str, error_trace: str) -> str:
        """Regenerate analysis code based on previous error.
        
        Args:
            user_query: User's analysis query
            df: DataFrame to analyze
            error_msg: Error message from failed execution
            error_trace: Full traceback from failed execution
            
        Returns:
            Corrected Python code string
        """
        df_info = f"Shape: {df.shape}\nColumns: {list(df.columns)}\nDtypes:\n{df.dtypes.to_dict()}"
        sample_data = df.head().to_dict()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a statistical analysis specialist. Fix the Python code that previously failed.

DataFrame Information:
{df_info}

Sample Data (first few rows):
{sample_data}

PREVIOUS ERROR (fix this):
{error_trace}

Analysis Code Requirements:
1. Use pandas (pd) and numpy (np) - both are available
2. Store ALL results in a dictionary named 'results'
3. Include descriptive labels for each result
4. DO NOT include import statements
5. Assume 'df' variable contains the data
6. Handle missing values gracefully
7. Convert numpy types to Python types for serialization
8. FIX the previous error - analyze what went wrong and correct it

Common Errors and Fixes:
- KeyError: Column doesn't exist → Check df.columns, use correct column names
- TypeError: Unsupported operand types → Ensure type compatibility, convert if needed
- ValueError: Invalid parameter value → Check parameter ranges and types
- AttributeError: Object has no attribute → Use correct method/attribute names
- ZeroDivisionError: Division by zero → Add checks before division

Output Format:
results = {{
    'metric_name': value,
    'another_metric': another_value
}}"""),
            ("user", "Fix the analysis code to analyze: {question}")
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
    
    def _format_results(self, results: Dict[str, Any]) -> str:
        """Format analysis results as readable string.
        
        Args:
            results: Dictionary of analysis results
            
        Returns:
            Formatted string
        """
        if not results:
            return "No analysis results"
        
        if 'error' in results:
            return f"Analysis error: {results['error']}"
        
        # Format results nicely
        lines = ["Statistical Analysis Results:"]
        for key, value in results.items():
            if isinstance(value, dict):
                lines.append(f"\n{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            else:
                lines.append(f"{key}: {value}")
        
        return "\n".join(lines)
    
    def _rag_select_analysis_methods(
        self,
        query: str,
        data_profile: Dict[str, Any],
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Use RAG to select appropriate analysis methods.
        
        Args:
            query: User query
            data_profile: Data profile from ProfilingAgent
            df: DataFrame
            
        Returns:
            List of method dictionaries with method cards
        """
        if not self.rag_system:
            return []
        
        # Detect analysis intent
        query_lower = query.lower()
        
        selected_methods = []
        
        # 1. Regression analysis
        if any(kw in query_lower for kw in ['regression', 'predict', 'relationship', 'impact', 'effect']):
            try:
                # Determine regression type
                if data_profile.get('has_non_normal'):
                    reg_query = "regression non-normal heteroscedasticity GLS robust"
                else:
                    reg_query = "linear regression OLS coefficients interpretation"
                
                method_cards = self.rag_system.retrieve_methods_for_statistics(
                    query=reg_query,
                    data_profile=data_profile,
                    k=2
                )
                
                if method_cards:
                    card, score = method_cards[0]
                    selected_methods.append({
                        "analysis_type": "regression",
                        "method_card": card,
                        "method_name": card.method_name,
                        "reasoning": f"Regression analysis requested. {card.when_to_use}",
                        "code_example": card.code_example,
                        "interpretation_guide": card.interpretation_guide,
                        "rag_score": score
                    })
                    print(f"[AnalysisAgent] RAG selected regression: {card.method_name} (score: {score:.2f})")
            except Exception as e:
                print(f"[AnalysisAgent] RAG regression query failed: {e}")
        
        # 2. Group comparison (ANOVA, t-test)
        if any(kw in query_lower for kw in ['compare', 'difference', 'between', 'groups', 'anova', 't-test']):
            try:
                # Check if parametric or non-parametric
                if data_profile.get('has_non_normal'):
                    comp_query = "compare groups mann whitney kruskal wallis non-parametric"
                else:
                    comp_query = "compare groups means anova t-test"
                
                method_cards = self.rag_system.retrieve_methods_for_statistics(
                    query=comp_query,
                    data_profile=data_profile,
                    k=2
                )
                
                if method_cards:
                    card, score = method_cards[0]
                    selected_methods.append({
                        "analysis_type": "group_comparison",
                        "method_card": card,
                        "method_name": card.method_name,
                        "reasoning": f"Group comparison requested. {card.when_to_use}",
                        "code_example": card.code_example,
                        "interpretation_guide": card.interpretation_guide,
                        "rag_score": score
                    })
                    print(f"[AnalysisAgent] RAG selected comparison: {card.method_name} (score: {score:.2f})")
            except Exception as e:
                print(f"[AnalysisAgent] RAG comparison query failed: {e}")
        
        # 3. Correlation analysis (handled by suggested tests from ProfilingAgent)
        if 'suggested_tests' in data_profile:
            for test in data_profile['suggested_tests']:
                if test.get('test_type') == 'correlation':
                    selected_methods.append({
                        "analysis_type": "correlation",
                        "method_card": test.get('method_card'),
                        "method_name": test.get('method_name'),
                        "reasoning": test.get('reason'),
                        "code_example": test.get('code_example'),
                        "rag_score": test.get('rag_score', 1.0)
                    })
                    print(f"[AnalysisAgent] Using ProfilingAgent suggestion: {test.get('method_name')}")
        
        return selected_methods
