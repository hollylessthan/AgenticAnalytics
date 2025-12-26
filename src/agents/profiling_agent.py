"""Profiling Agent for data quality assessment (read-only)."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from scipy import stats

from src.agents.base import BaseAgent, AgentState
from src.config import Config


class ProfilingAgent(BaseAgent):
    """Agent that performs data quality assessment without modifying data."""
    
    def __init__(self, config: Config):
        """Initialize Profiling Agent.
        
        Args:
            config: Configuration object
        """
        super().__init__(
            config=config,
            name="profiling_agent",
            description="Performs comprehensive data quality assessment (read-only)"
        )
        
        # Initialize RAG system for statistical test suggestions
        try:
            from src.rag.rag_system import RAGSystem
            self.rag_system = RAGSystem(config)
            print("[ProfilingAgent] RAG system initialized for test suggestions")
        except Exception as e:
            print(f"[ProfilingAgent] RAG system not available: {e}")
            self.rag_system = None
    
    def execute(self, state: AgentState) -> AgentState:
        """Execute profiling workflow with provenance check.
        
        Args:
            state: Current agent state
        Returns:
            Updated state with data profile
        """
        return self.execute_with_retry(state, self._execute_impl_with_provenance)


    def _compute_profile_provenance(self, df, source_type):
        # Use a hash of the DataFrame's values and columns for provenance, plus the source type
        import pandas as pd
        if not isinstance(df, pd.DataFrame):
            return None
        try:
            hash_val = str(pd.util.hash_pandas_object(df, index=True).sum())
        except Exception:
            hash_val = str(df.shape) + str(tuple(df.columns))
        return f"{source_type}:{hash_val}:{df.shape}:{tuple(df.columns)}"

    def _execute_impl_with_provenance(self, state: AgentState) -> AgentState:
        # Add to agent chain
        state.agent_chain.append("profiling_agent")

        # Get data source and type
        data_source = None
        source_type = None
        if state.preprocessed_dataframe is not None:
            data_source = state.preprocessed_dataframe
            source_type = "preprocessed"
            print("[ProfilingAgent] Profiling preprocessed dataframe")
        elif state.query_results is not None:
            data_source = state.query_results
            source_type = "query_results"
        elif state.cached_dataframe is not None:
            data_source = state.cached_dataframe
            source_type = "cached"
            print("[ProfilingAgent] Profiling cached dataframe")
        else:
            raise ValueError("No data available for profiling")

        df = self._prepare_dataframe(data_source)
        provenance = self._compute_profile_provenance(df, source_type)

        # Check provenance: only skip if profile exists and provenance matches
        if state.data_profile and state.data_profile.get("profile_provenance") == provenance:
            print(f"[ProfilingAgent] Using cached data profile (provenance match, source: {source_type})")
            return state

        if df.empty:
            raise ValueError("DataFrame is empty, cannot profile")

        # Generate comprehensive data profile
        print(f"[ProfilingAgent] Generating data profile for {len(df)} rows, {len(df.columns)} columns... (source: {source_type})")
        state.data_profile = self._generate_data_profile(df)
        state.data_profile["profile_provenance"] = provenance
        state.data_profile["profile_source_type"] = source_type

        # Add RAG-powered statistical test suggestions
        if self.rag_system:
            try:
                test_suggestions = self._suggest_statistical_tests(state.data_profile, state.query)
                if test_suggestions:
                    state.data_profile["suggested_tests"] = test_suggestions
                    print(f"[ProfilingAgent] RAG suggested {len(test_suggestions)} statistical tests")
            except Exception as e:
                print(f"[ProfilingAgent] RAG test suggestions failed: {e}")

        # Create summary for quick access
        state.data_summary = {
            "rows": len(df),
            "columns": len(df.columns),
            "missing_pct": state.data_profile["missing_values"]["total_pct"],
            "has_duplicates": state.data_profile["duplicates"]["has_duplicates"],
            "has_outliers": state.data_profile["has_outliers"],
            "has_non_normal": state.data_profile["has_non_normal"],
            "needs_scaling": state.data_profile["needs_scaling"],
            "has_quality_issues": self._has_quality_issues(state.data_profile)
        }

        print(f"[ProfilingAgent] Profile complete. Quality issues: {state.data_summary['has_quality_issues']} (source: {source_type})")

        return state
    
    def _execute_impl(self, state: AgentState) -> AgentState:
        """Implementation of profiling execution (wrapped in retry logic)."""
        try:
            # Add to agent chain
            state.agent_chain.append("profiling_agent")
            
            # Skip if profile already exists (cached)
            if state.data_profile:
                print("[ProfilingAgent] Using cached data profile")
                return state
            
            # Get data source
            data_source = None
            if state.preprocessed_dataframe is not None:
                data_source = state.preprocessed_dataframe
                print("[ProfilingAgent] Profiling preprocessed dataframe")
            elif state.query_results is not None:
                data_source = state.query_results
            elif state.cached_dataframe is not None:
                data_source = state.cached_dataframe
                print("[ProfilingAgent] Profiling cached dataframe")
            else:
                raise ValueError("No data available for profiling")
            
            df = self._prepare_dataframe(data_source)
            
            if df.empty:
                raise ValueError("DataFrame is empty, cannot profile")
            
            # Generate comprehensive data profile
            print(f"[ProfilingAgent] Generating data profile for {len(df)} rows, {len(df.columns)} columns...")
            state.data_profile = self._generate_data_profile(df)
            
            # Add RAG-powered statistical test suggestions
            if self.rag_system:
                try:
                    test_suggestions = self._suggest_statistical_tests(state.data_profile, state.query)
                    if test_suggestions:
                        state.data_profile["suggested_tests"] = test_suggestions
                        print(f"[ProfilingAgent] RAG suggested {len(test_suggestions)} statistical tests")
                except Exception as e:
                    print(f"[ProfilingAgent] RAG test suggestions failed: {e}")
            
            # Create summary for quick access
            state.data_summary = {
                "rows": len(df),
                "columns": len(df.columns),
                "missing_pct": state.data_profile["missing_values"]["total_pct"],
                "has_duplicates": state.data_profile["duplicates"]["has_duplicates"],
                "has_outliers": state.data_profile["has_outliers"],
                "has_non_normal": state.data_profile["has_non_normal"],
                "needs_scaling": state.data_profile["needs_scaling"],
                "has_quality_issues": self._has_quality_issues(state.data_profile)
            }
            
            print(f"[ProfilingAgent] Profile complete. Quality issues: {state.data_summary['has_quality_issues']}")
            
            return state
            
        except Exception as e:
            # Re-raise so retry logic can handle it
            raise
    
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
    
    def _has_quality_issues(self, profile: Dict[str, Any]) -> bool:
        """Check if data has significant quality issues.
        
        Args:
            profile: Data profile dictionary
            
        Returns:
            True if quality issues detected
        """
        return (
            profile["missing_values"]["total_pct"] > 5 or
            profile["duplicates"]["count"] > 0 or
            profile["has_outliers"] or
            profile["has_non_normal"] or
            len(profile["categorical_columns"]) > 0
        )
    
    def _generate_data_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive data profile with quality checks.
        
        This includes all important checks:
        - Missing values analysis
        - Duplicate detection
        - Data type analysis (categorical, numeric, datetime)
        - Distribution analysis (skewness, kurtosis, normality tests)
        - Outlier detection (IQR method)
        - Cardinality analysis
        - Correlation analysis
        - Scaling needs assessment
        
        Args:
            df: DataFrame to profile
            
        Returns:
            Dictionary with comprehensive data profile
        """
        profile = {
            "shape": {"rows": len(df), "cols": len(df.columns)},
            "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB",
        }
        
        # 1. Data type analysis
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        profile["dtypes"] = df.dtypes.astype(str).to_dict()
        profile["numeric_columns"] = numeric_cols
        profile["categorical_columns"] = categorical_cols
        profile["datetime_columns"] = datetime_cols
        
        # 2. Missing values analysis
        missing_count = df.isnull().sum().sum()
        missing_pct = (missing_count / df.size) * 100 if df.size > 0 else 0
        missing_by_col = {}
        
        for col in df.columns:
            col_missing = df[col].isnull().sum()
            if col_missing > 0:
                missing_by_col[col] = {
                    "count": int(col_missing),
                    "pct": float((col_missing / len(df)) * 100)
                }
        
        profile["missing_values"] = {
            "total_count": int(missing_count),
            "total_pct": float(missing_pct),
            "by_column": missing_by_col,
            "has_missing": missing_count > 0
        }
        
        # 3. Duplicate detection
        duplicate_count = df.duplicated().sum()
        profile["duplicates"] = {
            "count": int(duplicate_count),
            "pct": float((duplicate_count / len(df)) * 100) if len(df) > 0 else 0,
            "has_duplicates": duplicate_count > 0
        }
        
        # 4. Distribution analysis for numeric columns
        distributions = {}
        non_normal_features = []
        skewed_features = []
        
        for col in numeric_cols:
            try:
                col_data = df[col].dropna()
                if len(col_data) < 3:
                    continue
                
                # Calculate skewness and kurtosis
                skewness = float(col_data.skew())
                kurtosis = float(col_data.kurtosis())
                
                # Shapiro-Wilk test for normality (use sample if data is large)
                sample_size = min(5000, len(col_data))
                if len(col_data) > sample_size:
                    sample_data = col_data.sample(sample_size, random_state=42)
                else:
                    sample_data = col_data
                
                # Test normality
                is_normal = None
                shapiro_p = None
                if len(sample_data) >= 3:
                    try:
                        shapiro_stat, shapiro_p = stats.shapiro(sample_data)
                        shapiro_p = float(shapiro_p)
                        is_normal = shapiro_p > 0.05
                    except:
                        pass
                
                distributions[col] = {
                    "mean": float(col_data.mean()),
                    "std": float(col_data.std()),
                    "median": float(col_data.median()),
                    "min": float(col_data.min()),
                    "max": float(col_data.max()),
                    "skewness": skewness,
                    "kurtosis": kurtosis,
                    "is_normal": is_normal,
                    "shapiro_p_value": shapiro_p,
                    "quantiles": {
                        "q25": float(col_data.quantile(0.25)),
                        "q50": float(col_data.quantile(0.50)),
                        "q75": float(col_data.quantile(0.75)),
                        "q95": float(col_data.quantile(0.95)),
                        "q99": float(col_data.quantile(0.99))
                    }
                }
                
                # Track non-normal features
                if is_normal is False:
                    non_normal_features.append(col)
                
                # Track skewed features (threshold: |skewness| > 1)
                if abs(skewness) > 1:
                    skewed_features.append({"column": col, "skewness": skewness})
                    
            except Exception as e:
                print(f"[ProfilingAgent] Error profiling column {col}: {e}")
                continue
        
        profile["distributions"] = distributions
        profile["non_normal_features"] = non_normal_features
        profile["skewed_features"] = skewed_features
        profile["has_non_normal"] = len(non_normal_features) > 0
        profile["has_skew"] = len(skewed_features) > 0
        
        # Recommend correlation method based on normality
        if len(non_normal_features) > len(numeric_cols) * 0.5:
            profile["recommended_correlation"] = "spearman"
        else:
            profile["recommended_correlation"] = "pearson"
        
        # 5. Outlier detection (IQR method)
        outliers = {}
        for col in numeric_cols[:10]:  # Check first 10 numeric columns
            try:
                col_data = df[col].dropna()
                if len(col_data) < 4:
                    continue
                
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outlier_mask = (col_data < lower_bound) | (col_data > upper_bound)
                outlier_count = outlier_mask.sum()
                
                if outlier_count > 0:
                    outliers[col] = {
                        "count": int(outlier_count),
                        "pct": float((outlier_count / len(col_data)) * 100),
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound),
                        "method": "IQR"
                    }
            except:
                continue
        
        profile["outliers"] = outliers
        profile["has_outliers"] = len(outliers) > 0
        
        # 6. Cardinality analysis
        cardinality = {}
        for col in df.columns:
            unique_count = df[col].nunique()
            unique_pct = (unique_count / len(df)) * 100 if len(df) > 0 else 0
            
            cardinality[col] = {
                "unique_count": int(unique_count),
                "unique_pct": float(unique_pct),
                "is_high_cardinality": unique_pct > 50
            }
        
        profile["cardinality"] = cardinality
        
        # 7. Correlation analysis
        if len(numeric_cols) >= 2:
            try:
                corr_method = profile["recommended_correlation"]
                corr_matrix = df[numeric_cols].corr(method=corr_method)
                
                # Find high correlations (|corr| > 0.7, excluding diagonal)
                high_correlations = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.7:
                            high_correlations.append({
                                "col1": corr_matrix.columns[i],
                                "col2": corr_matrix.columns[j],
                                "correlation": float(corr_val)
                            })
                
                profile["correlations"] = {
                    "method": corr_method,
                    "high_correlations": high_correlations,
                    "has_multicollinearity": len(high_correlations) > 0
                }
            except:
                profile["correlations"] = {"method": "none", "high_correlations": [], "has_multicollinearity": False}
        else:
            profile["correlations"] = {"method": "none", "high_correlations": [], "has_multicollinearity": False}
        
        # 8. Scaling needs assessment
        needs_scaling = False
        if len(numeric_cols) >= 2:
            scales = []
            for col in numeric_cols[:10]:
                try:
                    std_val = df[col].std()
                    if pd.notna(std_val) and std_val > 0:
                        scales.append(std_val)
                except:
                    pass
            
            if scales and len(scales) >= 2:
                max_scale = max(scales)
                min_scale = min([s for s in scales if s > 0]) if any(s > 0 for s in scales) else 1
                if max_scale / min_scale > 10:  # Different orders of magnitude
                    needs_scaling = True
        
        profile["needs_scaling"] = needs_scaling
        
        # 9. Sample data
        profile["sample_data"] = df.head(3).to_dict()
        
        return profile
    
    def _suggest_statistical_tests(self, profile: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Use RAG to suggest appropriate statistical tests based on data profile.
        
        Args:
            profile: Data profile dictionary
            query: User query
            
        Returns:
            List of suggested statistical tests with method cards
        """
        if not self.rag_system:
            return []
        
        suggestions = []
        
        # 1. Normality tests (if data is non-normal)
        if profile.get("has_non_normal") and len(profile.get("non_normal_features", [])) > 0:
            try:
                method_cards = self.rag_system.retrieve_methods_for_statistics(
                    query="test normality distribution shapiro kolmogorov",
                    data_profile=profile,
                    k=2
                )
                
                if method_cards:
                    card, score = method_cards[0]
                    suggestions.append({
                        "test_type": "normality",
                        "method_card": card,
                        "method_name": card.method_name,
                        "reason": f"{len(profile['non_normal_features'])} features show non-normal distribution",
                        "suggestion": f"Use {card.method_name} to validate normality assumptions",
                        "affected_columns": profile["non_normal_features"][:5],
                        "code_example": card.code_example,
                        "rag_score": score
                    })
                    print(f"[ProfilingAgent] RAG suggested normality test: {card.method_name} (score: {score:.2f})")
            except Exception as e:
                print(f"[ProfilingAgent] RAG normality test query failed: {e}")
        
        # 2. Correlation tests (recommend appropriate correlation method)
        if len(profile.get("numeric_columns", [])) >= 2:
            # Use recommended correlation method from profile
            corr_method = profile.get("recommended_correlation", "pearson")
            
            if corr_method == "spearman" or corr_method == "kendall":
                try:
                    method_cards = self.rag_system.retrieve_methods_for_statistics(
                        query=f"{corr_method} correlation test non-parametric",
                        data_profile=profile,
                        k=2
                    )
                    
                    if method_cards:
                        card, score = method_cards[0]
                        suggestions.append({
                            "test_type": "correlation",
                            "method_card": card,
                            "method_name": card.method_name,
                            "reason": f"Non-normal data detected, recommend {corr_method} correlation",
                            "suggestion": f"Use {card.method_name} for robust correlation analysis",
                            "affected_columns": profile["numeric_columns"][:5],
                            "code_example": card.code_example,
                            "rag_score": score
                        })
                        print(f"[ProfilingAgent] RAG suggested correlation: {card.method_name} (score: {score:.2f})")
                except Exception as e:
                    print(f"[ProfilingAgent] RAG correlation test query failed: {e}")
        
        # 3. Group comparison tests (if categorical + numeric columns exist)
        categorical_cols = profile.get("categorical_columns", [])
        numeric_cols = profile.get("numeric_columns", [])
        
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            # Check if we should use parametric or non-parametric tests
            if profile.get("has_non_normal"):
                test_query = "mann whitney wilcoxon kruskal wallis non-parametric group comparison"
            else:
                test_query = "t-test anova group comparison means"
            
            try:
                method_cards = self.rag_system.retrieve_methods_for_statistics(
                    query=test_query,
                    data_profile=profile,
                    k=2
                )
                
                if method_cards:
                    card, score = method_cards[0]
                    suggestions.append({
                        "test_type": "group_comparison",
                        "method_card": card,
                        "method_name": card.method_name,
                        "reason": f"Categorical grouping variables found: {categorical_cols[:3]}",
                        "suggestion": f"Use {card.method_name} to compare groups across {numeric_cols[:3]}",
                        "affected_columns": {
                            "grouping": categorical_cols[:3],
                            "numeric": numeric_cols[:3]
                        },
                        "code_example": card.code_example,
                        "rag_score": score
                    })
                    print(f"[ProfilingAgent] RAG suggested group comparison: {card.method_name} (score: {score:.2f})")
            except Exception as e:
                print(f"[ProfilingAgent] RAG group comparison test query failed: {e}")
        
        return suggestions
