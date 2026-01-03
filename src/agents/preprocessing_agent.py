"""Preprocessing Agent for data quality checking and transformation."""

import pandas as pd
import numpy as np
import traceback
from typing import Dict, Any, Optional, Tuple, List
from scipy import stats
from langchain_core.prompts import ChatPromptTemplate

from src.agents.base import BaseAgent, AgentState
from src.config import Config
from src.utils.llm_factory import get_llm


class PreprocessingAgent(BaseAgent):
    def _validate_and_execute_code(self, code, current_df, state, is_fallback=False):
        """Agent that handles data quality assessment and preprocessing."""
        label = "(fallback)" if is_fallback else ""
        print(f"[PreprocessingAgent] Running validation step before execution {label}...")
        validated_code = self._validate_and_update_code(code, state.data_profile)
        # Ensure df_processed assignment is present (but don't overwrite if already present)
        if 'df_processed' not in validated_code:
            validated_code = validated_code.rstrip() + "\n\ndf_processed = df\n"
        if validated_code.strip() != code.strip():
            print(f"[PreprocessingAgent] Code was updated by validation step {label}.")
        else:
            print(f"[PreprocessingAgent] Validation step did not update code {label}.")
        print(f"[PreprocessingAgent] Code to be executed {label}:\n" + validated_code + "\n")
        state.preprocessing_code = validated_code
        df_processed, metadata = self._execute_preprocessing_code(validated_code, current_df)
        if df_processed is not None and isinstance(metadata, dict):
            state.preprocessed_dataframe = df_processed
            state.preprocessing_applied = metadata
            state.query_results = df_processed
            print(f"[PreprocessingAgent] Preprocessing complete {label}. Applied all transformations.")
            return True
        return False
    
    def __init__(self, config: Config):
        """Initialize Preprocessing Agent.
        
        Args:
            config: Configuration object
        """
        super().__init__(
            config=config,
            name="preprocessing_agent",
            description="Assesses data quality and applies preprocessing transformations"
        )
        self.llm = get_llm()
        
        # Initialize RAG system for preprocessing best practices
        try:
            from src.rag.rag_system import RAGSystem
            self.rag_system = RAGSystem(config)
        except Exception as e:
            print(f"[PreprocessingAgent] RAG system not available: {e}")
            self.rag_system = None
    
    def execute(self, state: AgentState) -> AgentState:
        """Execute preprocessing workflow.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with preprocessing results
        """
        return self.execute_with_retry(state, self._execute_impl)
    
    def _execute_impl(self, state: AgentState) -> AgentState:
        """Implementation of preprocessing execution (wrapped in retry logic)."""
        print(f"[DEBUG][PreprocessingAgent] needs_preprocessing_confirmation: {getattr(state, 'needs_preprocessing_confirmation', None)}")
        print(f"[DEBUG][PreprocessingAgent] preprocessing_approved: {getattr(state, 'preprocessing_approved', None)}")
        print(f"[DEBUG][PreprocessingAgent] preprocessing_needed: {getattr(state, 'preprocessing_needed', None)}")
        try:
            # Add to agent chain
            state.agent_chain.append("preprocessing_agent")
            
            # Check if preprocessed data already exists from previous query
            if state.preprocessed_dataframe is not None and state.preprocessing_applied:
                print(f"[PreprocessingAgent] ✅ Found existing preprocessed data from previous query")
                print(f"[PreprocessingAgent] Applied transformations: {state.preprocessing_applied}")
                
                # Ask user if they want to use existing preprocessed data
                state.needs_preprocessing_confirmation = True
                state.preprocessing_reuse_prompt = self._generate_reuse_prompt(state)
                return state
            
            # REQUIRE cached data profile (ProfilingAgent must run first)
            if not state.data_profile:
                raise ValueError("Data profile required. ProfilingAgent must run before PreprocessingAgent.")
            
            # Get data source
            data_source = None
            if state.query_results is not None:
                data_source = state.query_results
            elif state.cached_dataframe is not None:
                data_source = state.cached_dataframe
                print("[PreprocessingAgent] Using cached_dataframe as data source")
            else:
                raise ValueError("No data available for preprocessing")
            
            df = self._prepare_dataframe(data_source)
            
            if df.empty:
                raise ValueError("DataFrame is empty, cannot preprocess")
            
            # 1. Detect intent (if not already set)
            if not state.preprocessing_intent:
                state.preprocessing_intent = self._detect_intent(state.query)
                print(f"[PreprocessingAgent] Detected intent: {state.preprocessing_intent}")
            
            # 2. Use cached data profile (generated by ProfilingAgent)
            print(f"[PreprocessingAgent] Using cached profile for {len(df)} rows, {len(df.columns)} columns")
            print(f"[PreprocessingAgent] Data profile: {state.data_profile}")
            
            # 3. Query RAG for best practices (if available)
            rag_context = ""
            if self.rag_system:
                try:
                    rag_context = self._get_rag_context(state.query, state.preprocessing_intent)
                except Exception as e:
                    print(f"[PreprocessingAgent] RAG query failed: {e}")
            
            # 4. Assess quality and create recommendations (if not already done)
            if not state.preprocessing_needed:
                recommendations = self._create_recommendations(
                    state.data_profile, 
                    state.preprocessing_intent,
                    state.query
                )
                
                # Store recommendations for later access during code generation
                self._current_recommendations = recommendations
                
                if recommendations:
                    state.preprocessing_needed = {
                        "recommendations": recommendations,
                        "profile": state.data_profile,
                        "intent": state.preprocessing_intent,
                        "needs": self._convert_profile_to_needs(state.data_profile)
                    }
                    
                    print(f"[PreprocessingAgent] Found {len(recommendations)} preprocessing recommendations")
                    
                    # Pause for confirmation if in confirm mode
                    if state.preprocessing_mode == "confirm":
                        print("[PreprocessingAgent] Pausing for user confirmation")
                        state.needs_preprocessing_confirmation = True
                        return state
                    
                    # Auto-approve if in auto mode
                    elif state.preprocessing_mode == "auto":
                        print("[PreprocessingAgent] Auto mode - approving all recommendations")
                        state.preprocessing_approved = [r["action"] for r in recommendations]
                else:
                    print("[PreprocessingAgent] No preprocessing needed")
            else:
                # Retrieve recommendations from state
                self._current_recommendations = state.preprocessing_needed.get("recommendations", [])
            
            # 5. Apply all approved preprocessing in a single batch
            if state.preprocessing_approved and not state.preprocessed_dataframe:
                print(f"[PreprocessingAgent] Applying {len(state.preprocessing_approved)} preprocessing steps (single batch)")
                max_code_retries = 3
                last_error = None
                current_df = df.copy()
                preprocessing_code = ""
                for attempt in range(max_code_retries):
                    try:
                        if attempt == 0:
                            preprocessing_code = self._generate_preprocessing_code(
                                df=current_df,
                                profile=state.data_profile,
                                approved_actions=state.preprocessing_approved,
                                intent=state.preprocessing_intent,
                                rag_context=rag_context
                            )
                        else:
                            print(f"[PreprocessingAgent] Regenerating code for all actions (attempt {attempt + 1}/{max_code_retries}) due to: {str(last_error)[:100]}")
                            preprocessing_code = self._regenerate_preprocessing_code(
                                df=current_df,
                                profile=state.data_profile,
                                approved_actions=state.preprocessing_approved,
                                error_message=str(last_error),
                                failed_code=preprocessing_code
                            )
                        if self._validate_and_execute_code(preprocessing_code, current_df, state):
                            break
                    except Exception as e:
                        last_error = e
                        if attempt == max_code_retries - 1:
                            try:
                                preprocessing_code = self._generate_fallback_preprocessing_code(
                                    df=current_df,
                                    profile=state.data_profile,
                                    approved_actions=state.preprocessing_approved
                                )
                                state.preprocessing_code = preprocessing_code
                                if self._validate_and_execute_code(preprocessing_code, current_df, state, is_fallback=True):
                                    break
                            except Exception as fallback_e:
                                print(f"[PreprocessingAgent] Failed to apply all preprocessing after {max_code_retries} attempts. Error: {str(e)} | Fallback error: {str(fallback_e)}")
                                print("[PreprocessingAgent] Preprocessing failed. No valid code could be executed.")
                        elif attempt == max_code_retries - 1:
                            print("[PreprocessingAgent] Preprocessing failed. No valid code could be executed.")
            
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
    
    def _detect_intent(self, query: str) -> str:
        """Detect preprocessing intent from query.
        
        Args:
            query: User's natural language query
            
        Returns:
            Intent type: 'explore', 'analyze', or 'model'
        """
        query_lower = query.lower()
        
        # Model keywords (highest priority)
        model_keywords = [
            "predict", "forecast", "classify", "train", "model",
            "machine learning", "regression", "random forest",
            "logistic", "neural", "xgboost", "decision tree"
        ]
        
        # Analyze keywords (medium priority)
        analyze_keywords = [
            "correlat", "trend", "pattern", "relationship",
            "compare", "difference", "significant", "impact",
            "effect", "influence", "association"
        ]
        
        # Check keywords (prioritize model > analyze > explore)
        if any(kw in query_lower for kw in model_keywords):
            return "model"
        elif any(kw in query_lower for kw in analyze_keywords):
            return "analyze"
        else:
            return "explore"
    
    def _get_rag_context(self, query: str, intent: str) -> str:
        """Query RAG for preprocessing best practices.
        
        Args:
            query: User's query
            intent: Detected intent (explore/analyze/model)
            
        Returns:
            Retrieved RAG context string
        """
        if not self.rag_system:
            return ""
        
        rag_queries = [
            f"preprocessing best practices for {intent}",
            "data quality checks and validation",
            "handling missing values",
            "handling outliers",
            "feature scaling and normalization methods",
            "categorical encoding techniques"
        ]
        
        rag_context = ""
        for rag_query in rag_queries[:2]:  # Limit to avoid token overflow
            try:
                docs = self.rag_system.retrieve_context(rag_query, k=2)
                rag_context += "\n\n".join([doc.page_content for doc in docs])
            except:
                continue
        
        return rag_context[:2000]  # Limit context size
    
    def _rag_select_preprocessing_methods(
        self,
        profile: Dict[str, Any],
        intent: str
    ) -> List[Dict[str, Any]]:
        """Use RAG to select appropriate preprocessing methods based on data profile.
        
        Args:
            profile: Data profile from ProfilingAgent
            intent: Query intent (explore/analyze/model)
            
        Returns:
            List of preprocessing method recommendations with method cards
        """
        if not self.rag_system:
            return []
        
        recommendations = []
        
        # 1. Missing values imputation
        print('[DEBUG][PreprocessingAgent] Checking for missing values: ', profile["missing_values"]["has_missing"])
        if profile["missing_values"]["has_missing"]:
            missing_pct = profile["missing_values"]["total_pct"]
            # Build query for RAG
            if profile.get("has_outliers"):
                impute_query = "impute missing values numerical data robust outliers median"
            else:
                impute_query = "impute missing values numerical data mean median"
            try:
                method_cards = self.rag_system.retrieve_methods_for_imputation(
                    query=impute_query,
                    data_profile=profile,
                    k=2
                )
                if method_cards:
                    card, score = method_cards[0]
                    recommendations.append({
                        "action": "fill_missing",
                        "reason": f"{missing_pct:.1f}% missing values detected",
                        "method_card": card,
                        "method_name": card.method_name,
                        "suggestion": f"Use {card.method_name}: {card.when_to_use}",
                        "impact": "High - Required for analysis" if missing_pct > 10 else "Moderate",
                        "details": f"Affected columns: {list(profile['missing_values']['by_column'].keys())[:5]}",
                        "priority": 1 if missing_pct > 10 else 2,
                        "code_example": card.code_example,
                        "rag_score": score
                    })
                    print(f"[PreprocessingAgent] RAG selected: {card.method_name} (score: {score:.2f})")
            except Exception as e:
                print(f"[PreprocessingAgent] RAG imputation query failed: {e}")

        # 2. Categorical encoding
        if len(profile["categorical_columns"]) > 0:
            encode_query = "encode categorical features for modeling"
            try:
                method_cards = self.rag_system.retrieve_methods_for_encoding(
                    query=encode_query,
                    data_profile=profile,
                    k=2
                )
                if method_cards:
                    card, score = method_cards[0]
                    recommendations.append({
                        "action": "encode_categorical",
                        "reason": f"{len(profile['categorical_columns'])} categorical features found",
                        "method_card": card,
                        "method_name": card.method_name,
                        "suggestion": f"Use {card.method_name}: {card.when_to_use}",
                        "impact": "High - Required for ML models",
                        "details": f"Features: {profile['categorical_columns'][:5]}",
                        "priority": 1,
                        "code_example": card.code_example,
                        "rag_score": score
                    })
                    print(f"[PreprocessingAgent] RAG selected: {card.method_name} (score: {score:.2f})")
            except Exception as e:
                print(f"[PreprocessingAgent] RAG encoding query failed: {e}")

        # 3. Feature scaling
        if profile.get("needs_scaling") and intent == "model":
            # Check data characteristics for scaling method selection
            if profile.get("has_outliers"):
                scale_query = "scale features robust to outliers standardization"
            else:
                scale_query = "scale features standardization normalization zero mean unit variance"
            try:
                method_cards = self.rag_system.retrieve_methods_for_scaling(
                    query=scale_query,
                    data_profile=profile,
                    k=2
                )
                if method_cards:
                    card, score = method_cards[0]
                    recommendations.append({
                        "action": "scale_features",
                        "reason": "Features have different scales (important for distance-based models)",
                        "method_card": card,
                        "method_name": card.method_name,
                        "suggestion": f"Use {card.method_name}: {card.when_to_use}",
                        "impact": "High - Critical for linear models, SVM, Neural Networks",
                        "details": "Scales all numeric features",
                        "priority": 1,
                        "code_example": card.code_example,
                        "rag_score": score
                    })
                    print(f"[PreprocessingAgent] RAG selected: {card.method_name} (score: {score:.2f})")
            except Exception as e:
                print(f"[PreprocessingAgent] RAG scaling query failed: {e}")

        # 4. Outlier handling (RAG-based)
        outliers = profile.get("outliers", {})
        if len(outliers) > 0:
            try:
                method_cards = self.rag_system.retrieve_methods_for_outlier_handling(
                    query="cap outliers Mean ± 3 * StdDev winsorize",
                    data_profile=profile,
                    k=2
                )
                if method_cards:
                    card, score = method_cards[0]
                    recommendations.append({
                        "action": "handle_outliers",
                        "reason": f"Outliers detected in {len(outliers)} features",
                        "method_card": card,
                        "method_name": card.method_name,
                        "suggestion": f"Use {card.method_name}: {card.when_to_use}",
                        "impact": "Moderate - Prevents outliers from dominating model",
                        "details": f"Affected columns: {list(outliers.keys())[:5]}",
                        "priority": 2,
                        "code_example": card.code_example,
                        "rag_score": score
                    })
            except Exception as e:
                print(f"[PreprocessingAgent] RAG outlier handling query failed: {e}")

        # 5. Skewed features transformation (RAG-based)
        skewed_features = profile.get("skewed_features", [])
        print(f"[DEBUG][PreprocessingAgent] skewed_features: {skewed_features}")
        if len(skewed_features) > 0:
            try:
                method_cards = self.rag_system.retrieve_methods_for_transformation(
                    query="transform reduce skewness",
                    data_profile=profile,
                    k=1
                )
                print(f"[DEBUG][PreprocessingAgent] RAG returned for skewed transformation: {method_cards}")
                if method_cards:
                    card, score = method_cards[0]
                    recommendations.append({
                        "action": "transform_skewed",
                        "reason": f"{len(skewed_features)} features have high skewness (|skew| > 1)",
                        "suggestion": card.when_to_use,
                        "impact": "Moderate - Improves model performance for linear models",
                        "details": f"Skewed columns: {[f['column'] for f in skewed_features][:5]}",
                        "priority": 2,
                        "method_card": card,
                        "rag_score": score
                    })
            except Exception as e:
                print(f"[PreprocessingAgent] RAG skewed transform query failed: {e}")

        # Sort by priority
        recommendations.sort(key=lambda x: x.get("priority", 999))
        
        return recommendations
    
    def _convert_profile_to_needs(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Convert data profile to needs dict (for backward compatibility).
        
        Args:
            profile: Data profile dictionary
            
        Returns:
            Needs dictionary in old format
        """
        return {
            "missing_values": profile["missing_values"]["has_missing"],
            "missing_percentage": profile["missing_values"]["total_pct"],
            "missing_by_column": profile["missing_values"]["by_column"],
            "duplicates": profile["duplicates"]["count"],
            "has_duplicates": profile["duplicates"]["has_duplicates"],
            "categorical_features": profile["categorical_columns"],
            "numeric_features": profile["numeric_columns"],
            "needs_encoding": len(profile["categorical_columns"]) > 0,
            "skewed_features": profile["skewed_features"],
            "has_skew": profile["has_skew"],
            "non_normal_features": profile["non_normal_features"],
            "has_non_normal": profile["has_non_normal"],
            "outliers": profile["outliers"],
            "has_outliers": profile["has_outliers"],
            "needs_scaling": profile["needs_scaling"],
            "recommended_correlation": profile["recommended_correlation"]
        }
    
    def _create_recommendations(
        self, 
        profile: Dict[str, Any], 
        intent: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """Create preprocessing recommendations based on data profile and intent.
        
        Uses RAG-powered method card retrieval first, then falls back to rule-based
        recommendations if RAG is not available.
        
        Args:
            profile: Data profile dictionary
            intent: Query intent (explore/analyze/model)
            query: User's query
            
        Returns:
            List of recommendation dictionaries
        """
        # Try RAG-powered recommendations first
        if self.rag_system:
            try:
                rag_recommendations = self._rag_select_preprocessing_methods(profile, intent)
                if rag_recommendations:
                    print(f"[PreprocessingAgent] Using {len(rag_recommendations)} RAG-powered recommendations")
                    # Merge with rule-based recommendations for actions not covered by RAG
                    rule_based = self._create_rule_based_recommendations(profile, intent)
                    
                    # Add rule-based recommendations that aren't covered by RAG
                    rag_actions = {r["action"] for r in rag_recommendations}
                    for rec in rule_based:
                        if rec["action"] not in rag_actions:
                            rag_recommendations.append(rec)
                    
                    return rag_recommendations
            except Exception as e:
                print(f"[PreprocessingAgent] RAG recommendations failed: {e}, using rule-based fallback")
        
        # Fallback to rule-based recommendations
        print("[PreprocessingAgent] Using rule-based recommendations")
        return self._create_rule_based_recommendations(profile, intent)
    
    def _create_rule_based_recommendations(
        self,
        profile: Dict[str, Any],
        intent: str
    ) -> List[Dict[str, Any]]:
        """Create rule-based preprocessing recommendations (fallback when RAG unavailable).
        
        This uses the same logic as the hardcoded PreprocessingChecker to ensure
        all important checks are covered.
        
        Args:
            profile: Data profile dictionary
            intent: Query intent (explore/analyze/model)
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        missing_info = profile["missing_values"]
        missing_pct = missing_info["total_pct"]
        missing_by_col = missing_info["by_column"]
        
        duplicates_info = profile["duplicates"]
        duplicate_count = duplicates_info["count"]
        
        categorical_cols = profile["categorical_columns"]
        skewed_features = profile["skewed_features"]
        non_normal_features = profile["non_normal_features"]
        outliers = profile["outliers"]
        needs_scaling = profile["needs_scaling"]
        
        # Different recommendations based on intent
        if intent == "explore":
            # Explore mode: Minimal preprocessing, only critical issues
            if missing_pct >= 20:  # Only flag if >20% missing
                recommendations.append({
                    "action": "fill_missing",
                    "reason": f"{missing_pct:.1f}% missing values detected",
                    "suggestion": "Fill with median (numerical) / mode (categorical)",
                    "impact": "Moderate - Required for complete exploration",
                    "details": f"Affected columns: {list(missing_by_col.keys())[:5]}",
                    "priority": 2
                })
        
        elif intent == "analyze":
            # Analyze mode: Focus on statistical validity
            if missing_pct >= 5:
                recommendations.append({
                    "action": "fill_missing",
                    "reason": f"{missing_pct:.1f}% missing values across {len(missing_by_col)} columns",
                    "suggestion": "Fill numerical with median, categorical with mode",
                    "impact": "Moderate - Allows complete analysis but may introduce bias",
                    "details": f"Affected columns: {list(missing_by_col.keys())[:5]}",
                    "priority": 1
                })
            
            if duplicate_count > 0:
                recommendations.append({
                    "action": "remove_duplicates",
                    "reason": f"{duplicate_count} duplicate rows found",
                    "suggestion": "Remove duplicate rows",
                    "impact": "Low - Cleans data without information loss",
                    "details": f"{duplicate_count} rows ({duplicates_info['pct']:.1f}%)",
                    "priority": 3
                })
            
            # Distribution-based recommendations
            if profile["has_non_normal"] and len(non_normal_features) > 0:
                recommendations.append({
                    "action": "check_distribution",
                    "reason": f"{len(non_normal_features)} features are non-normally distributed",
                    "suggestion": f"Use {profile['recommended_correlation']} correlation instead of Pearson",
                    "impact": "High - Affects validity of correlation and statistical tests",
                    "details": f"Non-normal features: {non_normal_features[:5]}",
                    "priority": 1
                })
        
        elif intent == "model":
            # Model mode: Full preprocessing pipeline
            
            # Missing values (always recommend if >5%)
            if missing_pct >= 5:
                recommendations.append({
                    "action": "fill_missing",
                    "reason": f"{missing_pct:.1f}% missing values detected",
                    "suggestion": "Fill with median (numerical) / mode (categorical)",
                    "impact": "High - Required for model training",
                    "details": f"Columns: {list(missing_by_col.keys())[:5]}",
                    "priority": 1
                })
            
            # Categorical encoding (always recommend)
            if len(categorical_cols) > 0:
                recommendations.append({
                    "action": "encode_categorical",
                    "reason": f"{len(categorical_cols)} categorical features found",
                    "suggestion": "Label encoding for ordinal, OneHot for nominal",
                    "impact": "High - Required for most ML models",
                    "details": f"Features: {categorical_cols[:5]}",
                    "priority": 1
                })
            
            
            # Outlier handling
            if len(outliers) > 0:
                recommendations.append({
                    "action": "handle_outliers",
                    "reason": f"Outliers detected in {len(outliers)} features",
                    "suggestion": "Cap outliers using STD method (Mean ± 3 * StdDev)",
                    "impact": "Moderate - Prevents outliers from dominating model",
                    "details": f"Affected columns: {list(outliers.keys())[:5]}",
                    "priority": 2
                })
            
            # Distribution normality (inform about model choice)
            if profile["has_non_normal"] and len(non_normal_features) > 0:
                recommendations.append({
                    "action": "check_distribution",
                    "reason": f"{len(non_normal_features)}/{len(profile['numeric_columns'])} features are non-normally distributed",
                    "suggestion": "Consider tree-based models (no normality assumption) or transform skewed features",
                    "impact": "High - Affects model choice and performance",
                    "details": f"Non-normal: {non_normal_features[:5]}. Use Random Forest/XGBoost or transform data.",
                    "priority": 1
                })
            
            # Feature scaling (always recommend if needed)
            if needs_scaling:
                recommendations.append({
                    "action": "scale_features",
                    "reason": "Features have different scales (important for distance-based models)",
                    "suggestion": "StandardScaler (zero mean, unit variance)",
                    "impact": "High - Critical for linear models, SVM, Neural Networks",
                    "details": "Scales all numeric features",
                    "priority": 1
                })
            
            # Remove duplicates
            if duplicate_count > 0:
                recommendations.append({
                    "action": "remove_duplicates",
                    "reason": f"{duplicate_count} duplicate rows found",
                    "suggestion": "Remove duplicate rows before training",
                    "impact": "Moderate - Prevents data leakage",
                    "details": f"{duplicate_count} rows ({duplicates_info['pct']:.1f}%)",
                    "priority": 2
                })
        
        # Sort by priority (lower number = higher priority)
        recommendations.sort(key=lambda x: x.get("priority", 999))
        
        return recommendations
    
    def _generate_preprocessing_code(
        self,
        df: pd.DataFrame,
        profile: Dict[str, Any],
        approved_actions: List[str],
        intent: str,
        rag_context: str
    ) -> str:
        """Generate preprocessing code using LLM with RAG guidance.
        
        Args:
            df: DataFrame to preprocess
            profile: Data profile dictionary
            approved_actions: List of approved preprocessing actions
            intent: Query intent
            rag_context: Retrieved RAG context (legacy, kept for compatibility)
            
        Returns:
            Python preprocessing code
        """
        # Build a concise summary
        shape = profile.get('shape', {})
        n_rows = shape.get('rows', 'unknown')
        n_cols = shape.get('cols', 'unknown')
        missing_values = profile.get('missing_values', {})
        missing_total_pct = missing_values.get('total_pct', 0.0)
        categorical_columns = profile.get('categorical_columns', [])
        needs_scaling = profile.get('needs_scaling', False)
        summary = f"Rows: {n_rows}, Cols: {n_cols}, Missing: {missing_total_pct:.1f}%, Cat: {categorical_columns[:3]}, Scaling: {needs_scaling}"
        print(approved_actions)
        # Concise system prompt
        system_message = f"""
You are a data preprocessing expert. Generate Python code to preprocess a pandas DataFrame named 'df'.

Context: {summary}
Approved actions: {approved_actions}
Intent: {intent}

Requirements:
- Only apply the user-approved actions from the list above.
- Store the preprocessed DataFrame in 'df_processed'.
- Store a metadata dict in 'preprocessing_metadata' describing what was applied.
- Split Data First: Separate df into features (X) and target (y) immediately.
- Imputation (if approved):  If target (y) is missing, drop the entire row. Do NOT impute y. Apply imputation method to missing feature values (x).
- Encoding (if approved): If Classification, apply LabelEncoder to target (y). Apply Encoding method to categorical features."
- Transform (if approved): If Regression and target (y) is right skewed, apply np.log1p. Apply transform method to numeric features.
- Outlier clipping (if approved): Do NOT apply outlier clipping to y. Apply capping method to numeric features.
- Scaling (if approved): Do NOT apply scaling to y. Apply scaling method to numeric features.
- Do not print anything in the code.
- For numeric features, always transform first, scale second, and cap outliers as the final step.

Code structure example:
df_processed = df.copy()
preprocessing_metadata = {{}}
if 'fill_missing' in approved_actions:
    # Fill missing values logic
    preprocessing_metadata['filled_columns'] = list_of_filled_columns
if 'encode_categorical' in approved_actions:
    # Encode categorical logic
    preprocessing_metadata['encoded_columns'] = list_of_encoded_columns
if 'handle_outliers' in approved_actions:
    # Cap outliers using Mean ± 3 * StdDev for outliers
# ... etc for other actions

Do NOT use ellipsis (`...`) or curly braces (`{{...}}`) as placeholders. Do NOT include import statements. Return only the code.
"""
        user_message = f"Generate preprocessing code for approved actions: {approved_actions}"
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("user", user_message)
        ])
        try:
            response = self.llm.invoke(prompt.format_messages())
            code = response.content.strip()
            if code.startswith("```python"):
                code = code[9:]
            if code.startswith("```"):
                code = code[3:]
            if code.endswith("```"):
                code = code[:-3]            

            print("\n[PreprocessingAgent] Generated preprocessing code:\n" + code + "\n")
        except Exception as e:
            import traceback
            print(f"[PreprocessingAgent] Code generation failed: {e}")
            print(traceback.format_exc())
            raise

        # Always run validation if code was generated, with retry/fix loop
        max_code_retries = getattr(self.config, 'max_code_retries', 3)
        last_error = None
        validated_code = code
        for attempt in range(max_code_retries):
            try:
                code_to_validate = validated_code
                print(f"[PreprocessingAgent] Running LLM validation step (attempt {attempt+1}/{max_code_retries})...")
                validated_code = self._validate_and_update_code(code_to_validate, profile)
                return validated_code.strip()
            except Exception as e:
                last_error = e
                print(f"[PreprocessingAgent] Validation step failed: {e}")
                print(traceback.format_exc())
                # Use LLM to fix the code based on the error
                validated_code = self._regenerate_preprocessing_code(
                    df=df,
                    profile=profile,
                    approved_actions=approved_actions,
                    error_message=str(e),
                    failed_code=validated_code
                )
        # If all retries fail, return the last attempted code
        print("[PreprocessingAgent] Validation failed after retries. Returning last attempted code.")
        return validated_code.strip()

    def _validate_and_update_code(self, code: str, profile: dict) -> str:
        """Use LLM to validate and update code if it does not follow instructions."""
        print("\n[PreprocessingAgent] Code before LLM validation:\n" + code + "\n")
        validation_system_message = """
Check the following Python preprocessing code for these requirements:

1. All skewed features (skewness > 1 or < -1) should be transformed using sklearn's PowerTransformer. Right skewed target should be transformed using np.log1p.
2. All approved actions must be implemented.
3. Outliers should be capped using Mean ± 3 * StdDev method.
4. For numeric features, always transform first, scale second, and cap outliers last.
5. Rows with missing target values should be dropped as the final step.

If the code does not follow these, rewrite only the relevant parts to comply and return the updated code. Otherwise, return the code unchanged.
Return only the corrected code, no explanations, no ```python ``` formatting or any code block markers.

"""
        validation_prompt = ChatPromptTemplate.from_messages([
            ("system", validation_system_message),
            ("user", code)
        ])
        try:
            response = self.llm.invoke(validation_prompt.format_messages())
            validated_code = response.content.strip()
            print("\n[PreprocessingAgent] LLM validated/updated preprocessing code:\n" + validated_code + "\n")
            return validated_code
        except Exception as e:
            print(f"[PreprocessingAgent] LLM validation failed: {e}")
            return code

    
    def _generate_fallback_preprocessing_code(
        self,
        df: pd.DataFrame,
        profile: Dict[str, Any],
        approved_actions: List[str]
    ) -> str:
        """Raise error instead of returning hardcoded preprocessing code."""
        raise RuntimeError("LLM code generation failed and fallback preprocessing is disabled.")
    
    def _regenerate_preprocessing_code(
        self,
        df: pd.DataFrame,
        profile: Dict[str, Any],
        approved_actions: List[str],
        error_message: str,
        failed_code: str
    ) -> str:
        """Regenerate preprocessing code after execution failure.
        
        Args:
            df: Input DataFrame
            profile: Data profile
            approved_actions: Approved preprocessing actions
            error_message: Error from previous attempt
            failed_code: Code that failed
            
        Returns:
            Regenerated preprocessing code
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data preprocessing expert. The previous preprocessing code failed.

Your task: Fix the code based on the error message.

Common issues to fix:
- Invalid f-string variable names (use {{}} for literal braces, not attribute access)
- ```python ``` formatting (remove any code block markers)
- Column name mismatches (check actual column names)
- Type mismatches (ensure correct data types)
- Print issues (remove any print statements)
- Target variable missed to be processed (apply transformations or encoding to target if approved)
- Target variable handling (do not impute, scale, or cap outliers on target variable)
- Missing imports
- Fuctions defined but not used (don't define any functions)
- Wrong preprocessing order (For numeric features, always transform first, scale second, and cap outliers as the final step).
- Missing values in target (Drop rows with missing target values as the final step)

Rules:
- Use simple variable names in f-strings (no dots, brackets, or attribute access)
- Escape literal braces with double braces {{}}


Return ONLY executable Python code, no explanations."""),
            ("user", """DataFrame columns: {columns}
Approved actions: {actions}

Failed code:
```python
{failed_code}
```

Error message:
{error}

Fix the code:""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({
            "columns": list(df.columns),
            "actions": approved_actions,
            "failed_code": failed_code,
            "error": error_message
        })
        
        # Extract code from response
        code = response.content.strip()
        if "```python" in code:
            code = code.split("```python")[1].split("```",1)[0].strip()
        elif "```" in code:
            code = code.split("```",1)[1].split("```",1)[0].strip()
        print("\n[PreprocessingAgent] Regenerated preprocessing code after failure:\n" + code + "\n")
        return code
        return code
    
    def _execute_preprocessing_code(
        self,
        code: str,
        df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Execute preprocessing code safely.
        
        Args:
            code: Python preprocessing code
            df: Original dataframe
            
        Returns:
            Tuple of (preprocessed_dataframe, metadata_dict)
        """
        from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, LabelEncoder
        from sklearn.impute import SimpleImputer
        
        # Create safe execution environment
        local_vars = {
            'df': df,
            'pd': pd,
            'np': np,
            'StandardScaler': StandardScaler,
            'MinMaxScaler': MinMaxScaler,
            'RobustScaler': RobustScaler,
            'LabelEncoder': LabelEncoder,
            'SimpleImputer': SimpleImputer,
            'df_processed': None,
            'preprocessing_metadata': {},
            'approved_actions': []
        }
        
        try:
            # Print the code before execution for debugging
            print("\n[PreprocessingAgent] Executing preprocessing code:\n" + code + "\n")
            exec(code, {"__builtins__": __builtins__}, local_vars)
            df_processed = local_vars.get('df_processed')
            metadata = local_vars.get('preprocessing_metadata', {})
            if df_processed is None:
                raise ValueError("Preprocessing code did not produce df_processed")
            if df_processed.empty:
                raise ValueError("Preprocessing resulted in empty dataframe")
            if len(df_processed) < len(df) * 0.5:
                print(f"[PreprocessingAgent] Warning: Preprocessing removed >50% of data ({len(df)} -> {len(df_processed)})")
            return df_processed, metadata
        except Exception as e:
            print(f"[PreprocessingAgent] Preprocessing execution failed: {str(e)}")
            print(f"[PreprocessingAgent] Traceback:\n{traceback.format_exc()}")
            print("\n[PreprocessingAgent] Code that caused error (printing for debugging):\n" + code + "\n")
            # Always print the code, even if execution fails
            return df, {"error": f"Preprocessing failed: {str(e)}"}
    
    def _generate_reuse_prompt(self, state: AgentState) -> str:
        """Generate a user-friendly prompt asking if they want to reuse preprocessed data.
        
        Args:
            state: Current state with preprocessing history
            
        Returns:
            Formatted prompt string with data preview and applied transformations
        """
        import pandas as pd
        
        prompt_lines = []
        prompt_lines.append("🔧 **Preprocessed Data Available**")
        prompt_lines.append("")
        prompt_lines.append("I found preprocessed data from your previous query. Here's what was done:")
        prompt_lines.append("")
        
        # Show applied transformations
        prompt_lines.append("**Applied Transformations:**")
        for i, step in enumerate(state.preprocessing_applied, 1):
            prompt_lines.append(f"  {i}. {step}")
        prompt_lines.append("")
        
        # Show data preview (top 5 rows)
        if state.preprocessed_dataframe is not None:
            df = state.preprocessed_dataframe
            prompt_lines.append(f"**Preprocessed Data Preview** ({len(df)} rows × {len(df.columns)} columns):")
            prompt_lines.append("```")
            prompt_lines.append(df.head(5).to_string())
            prompt_lines.append("```")
            prompt_lines.append("")
        
        prompt_lines.append("**Options:**")
        prompt_lines.append("1. ✅ **Use this preprocessed data** - Continue with modeling on clean data")
        prompt_lines.append("2. 🔄 **Reprocess from scratch** - Apply new transformations")
        prompt_lines.append("")
        prompt_lines.append("Would you like to use the existing preprocessed data for modeling?")
        
        return "\n".join(prompt_lines)

