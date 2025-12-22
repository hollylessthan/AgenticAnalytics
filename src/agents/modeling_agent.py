"""Modeling Agent for ML model selection and training using RAG."""

import pandas as pd
import numpy as np
import traceback
from typing import Dict, Any, Optional, List, Tuple
from langchain_core.prompts import ChatPromptTemplate

from src.agents.base import BaseAgent, AgentState
from src.config import Config
from src.utils.llm_factory import get_llm
from src.rag.method_card import MethodCard


class ModelingAgent(BaseAgent):
    """Agent that selects and trains ML models using RAG-powered method cards."""
    
    def __init__(self, config: Config):
        """Initialize Modeling Agent.
        
        Args:
            config: Configuration object
        """
        super().__init__(
            config=config,
            name="modeling_agent",
            description="Selects and trains machine learning models using RAG-powered method cards"
        )
        self.llm = get_llm()
        
        # Initialize RAG system for method card retrieval
        try:
            from src.rag.rag_system import RAGSystem
            self.rag_system = RAGSystem(config)
            print("[ModelingAgent] RAG system initialized for model selection")
        except Exception as e:
            print(f"[ModelingAgent] Warning: RAG system not available: {e}")
            self.rag_system = None
    
    def execute(self, state: AgentState) -> AgentState:
        """Execute modeling workflow with RAG-based model selection.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with model training results
        """
        return self.execute_with_retry(state, self._execute_impl)
    
    def _prepare_dataframe(self, data: Any) -> pd.DataFrame:
        """Convert query results to DataFrame.
        
        Args:
            data: Query results (DataFrame, list, dict, etc.)
            
        Returns:
            pandas DataFrame
        """
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, list):
            return pd.DataFrame(data)
        else:
            return pd.DataFrame([data])
    
    def _execute_impl(self, state: AgentState) -> AgentState:
        """Implementation of modeling execution (wrapped in retry logic)."""
        try:
            # Add to agent chain
            state.agent_chain.append("modeling_agent")
            
            # Get data source - prefer preprocessed data if available
            data_source = None
            if state.preprocessed_dataframe is not None:
                data_source = state.preprocessed_dataframe
                print("[ModelingAgent] Using preprocessed dataframe")
            elif state.query_results is not None:
                data_source = state.query_results
            elif state.cached_dataframe is not None:
                data_source = state.cached_dataframe
                print("[ModelingAgent] Using cached_dataframe as data source")
            else:
                raise ValueError("No data available for modeling")
            
            df = self._prepare_dataframe(data_source)
            
            if df.empty:
                raise ValueError("DataFrame is empty, cannot train model")
            
            # Step 1: Detect modeling intent and problem type
            modeling_intent = self._detect_modeling_intent(
                query=state.query,
                df=df,
                conversation_history=state.conversation_history
            )
            print(f"[ModelingAgent] Detected intent: {modeling_intent}")
            
            # Step 2: RAG-based model selection
            if self.rag_system:
                selected_models = self._rag_select_models(
                    query=state.query,
                    modeling_intent=modeling_intent,
                    data_profile=state.data_profile,
                    df=df
                )
            else:
                # Fallback: LLM-only selection
                selected_models = self._llm_select_models(state.query, df, modeling_intent)
            
            if not selected_models:
                raise ValueError("No suitable models found for this problem")
            
            print(f"[ModelingAgent] Selected {len(selected_models)} candidate model(s)")
            
            # Step 3: Generate and execute training code with error-aware retries
            best_model = selected_models[0]  # Use top-ranked model
            print(f"[ModelingAgent] Training model: {best_model['name']}")
            
            max_code_retries = 3
            training_results = None
            error_message = None
            failed_code = None
            
            for attempt in range(max_code_retries):
                try:
                    if attempt == 0:
                        # First attempt: generate fresh code
                        training_code = self._generate_training_code(
                            model_info=best_model,
                            df=df,
                            modeling_intent=modeling_intent,
                            query=state.query
                        )
                    else:
                        # Retry: regenerate code based on error
                        print(f"[ModelingAgent] Regenerating code based on error (attempt {attempt + 1}/{max_code_retries})")
                        training_code = self._regenerate_training_code(
                            model_info=best_model,
                            df=df,
                            modeling_intent=modeling_intent,
                            query=state.query,
                            error_message=error_message,
                            failed_code=failed_code
                        )
                    
                    # Store code in state for UI display
                    state.modeling_code = training_code
                    
                    # Execute training code
                    training_results = self._execute_training_code(training_code, df)
                    
                    if 'error' not in training_results:
                        print(f"[ModelingAgent] Successfully trained model")
                        break
                    else:
                        error_message = training_results.get('error', 'Unknown error')
                        failed_code = training_code
                        
                except Exception as e:
                    error_message = str(e)
                    failed_code = training_code if 'training_code' in locals() else None
                    if attempt == max_code_retries - 1:
                        raise
            
            if training_results is None or 'error' in training_results:
                raise ValueError(f"Failed to train model after {max_code_retries} attempts")

            
            # Generate model summary (like statsmodels/sklearn output)
            model_summary = self._generate_model_summary(
                model_info=best_model,
                training_results=training_results,
                modeling_intent=modeling_intent
            )
            
            # Step 4: Store results in state
            state.model_results = {
                "selected_model": best_model['name'],
                "model_card": best_model.get('method_card'),
                "candidates": selected_models,
                "training_code": training_code,
                "metrics": training_results.get('metrics', {}),
                "model_object": training_results.get('model'),
                "predictions": training_results.get('predictions'),
                "feature_importance": training_results.get('feature_importance'),
                "interpretation": self._interpret_results(best_model, training_results)
            }
            
            # Store formatted model summary for UI display
            state.model_summary = model_summary
            
            print(f"[ModelingAgent] ✓ Model training complete")
            print(f"[ModelingAgent] Metrics: {training_results.get('metrics', {})}")
            
            return state
            
        except Exception as e:
            print(f"[ModelingAgent] Error: {str(e)}")
            print(traceback.format_exc())
            state.error = str(e)
            return state
    
    def _detect_modeling_intent(self, query: str, df: pd.DataFrame, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Detect modeling problem type and target variable using LLM.
        
        Args:
            query: User query
            df: DataFrame
            conversation_history: Previous conversation context
            
        Returns:
            Dict with problem_type, target, features
        """
        # Build conversation context
        context = ""
        if conversation_history and len(conversation_history) > 0:
            context = "\n\nPrevious Conversation Context:\n"
            for i, turn in enumerate(conversation_history):  # Use all available history
                context += f"User: {turn.get('user', '')}\n"
                if turn.get('assistant'):
                    # Truncate long responses
                    assistant_msg = turn['assistant'][:200] + "..." if len(turn['assistant']) > 200 else turn['assistant']
                    context += f"Assistant: {assistant_msg}\n"
            context += "\nUse this context to better understand what the user wants to predict.\n"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data science expert. Analyze the query and dataset to identify the modeling task.

Your job:
1. Determine the problem type (classification, regression, clustering)
2. Identify which column is the target/dependent variable
3. Identify which columns are features/independent variables
4. For classification: determine if binary or multi-class

Analysis Guidelines:
- Read the query carefully - what is the user trying to PREDICT?
- Check column names and data types to find the target
- Numeric targets with many unique values → regression
- Categorical targets or numeric with few unique values → classification
- No clear target mentioned → clustering
- The target MUST be an actual column from the available columns list
- Review conversation history (if provided) for context about what user wants to predict{context}

Available columns: {columns}
Data types: {dtypes}

First 3 rows of data:
{sample_data}

Respond in JSON format:
{{
    "problem_type": "classification|regression|clustering",
    "target_column": "exact_column_name",
    "is_binary": true|false|null,
    "feature_columns": ["col1", "col2", ...],
    "reasoning": "explain your decision"
}}"""),
            ("user", "{query}")
        ])
        
        # Get sample of data
        sample_data = df.head(3).to_string()
        columns = list(df.columns)
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        
        response = self.llm.invoke(prompt.format_messages(
            query=query,
            columns=columns,
            dtypes=dtypes,
            sample_data=sample_data,
            context=context
        ))
        
        # Parse JSON response
        import json
        try:
            intent = json.loads(response.content)
            print(f"[ModelingAgent] Intent reasoning: {intent.get('reasoning', 'N/A')}")
            
            # Validate target column exists
            target_col = intent.get('target_column')
            if target_col not in df.columns:
                print(f"[ModelingAgent] Warning: LLM suggested non-existent target '{target_col}'")
                # Try to find closest match
                target_col_lower = target_col.lower() if target_col else ""
                for col in df.columns:
                    if target_col_lower in col.lower() or col.lower() in target_col_lower:
                        print(f"[ModelingAgent] Found close match: '{col}'")
                        intent['target_column'] = col
                        intent['feature_columns'] = [c for c in df.columns if c != col]
                        return intent
                
                # If no match found, use fallback
                print(f"[ModelingAgent] No match found, using fallback")
                raise ValueError("Target column not found")
            
            return intent
            
        except Exception as e:
            print(f"[ModelingAgent] LLM intent detection failed: {e}")
            # Fallback: Use smart heuristic based on data types
            return self._fallback_intent_detection(df)
    
    def _fallback_intent_detection(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Fallback heuristic for intent detection when LLM fails.
        
        Args:
            df: DataFrame
            
        Returns:
            Dict with problem_type, target, features
        """
        # Find numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            # Use last numeric column as target
            # Check if it looks like regression (many unique values) or classification (few)
            target = numeric_cols[-1]
            n_unique = df[target].nunique()
            n_samples = len(df)
            
            # If unique values > 20% of samples, likely regression
            if n_unique > 0.2 * n_samples:
                problem_type = "regression"
                is_binary = None
            else:
                problem_type = "classification"
                is_binary = (n_unique == 2)
            
            features = [col for col in df.columns if col != target]
            return {
                "problem_type": problem_type,
                "target_column": target,
                "is_binary": is_binary,
                "feature_columns": features,
                "reasoning": f"Fallback: Selected last numeric column '{target}' with {n_unique} unique values"
            }
        else:
            # No numeric columns, use last column
            target = df.columns[-1]
            features = list(df.columns[:-1])
            n_unique = df[target].nunique()
            return {
                "problem_type": "classification",
                "target_column": target,
                "is_binary": (n_unique == 2),
                "feature_columns": features,
                "reasoning": f"Fallback: Selected last column '{target}'"
            }
    
    def _rag_select_models(
        self,
        query: str,
        modeling_intent: Dict[str, Any],
        data_profile: Optional[Dict[str, Any]],
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Use RAG to select appropriate models based on problem type and data characteristics.
        
        Args:
            query: User query
            modeling_intent: Detected modeling intent
            data_profile: Data profile from ProfilingAgent
            df: DataFrame
            
        Returns:
            List of model dictionaries with method cards
        """
        # Build enhanced query with problem context
        problem_type = modeling_intent.get('problem_type', 'classification')
        is_binary = modeling_intent.get('is_binary', True)
        n_samples = len(df)
        n_features = len(modeling_intent.get('feature_columns', []))
        
        # Create RAG query
        if problem_type == 'classification':
            if is_binary:
                rag_query = f"binary classification model {n_samples} samples {n_features} features"
            else:
                rag_query = f"multi-class classification model {n_samples} samples {n_features} features"
        elif problem_type == 'regression':
            rag_query = f"regression model predict continuous {n_samples} samples {n_features} features"
        else:
            rag_query = f"{problem_type} model {n_samples} samples"
        
        # Add data characteristics to query
        if data_profile:
            if data_profile.get('has_non_normal'):
                rag_query += " non-normal distribution"
            if data_profile.get('has_outliers'):
                rag_query += " outliers"
            if data_profile.get('missing_values', {}).get('total_pct', 0) > 0:
                rag_query += " missing values"
        
        print(f"[ModelingAgent] RAG Query: {rag_query}")
        
        # Retrieve method cards
        try:
            method_cards: List[Tuple[MethodCard, float]] = self.rag_system.retrieve_methods_for_modeling(
                query=rag_query,
                data_profile=data_profile,
                k=5
            )
            
            if not method_cards:
                print("[ModelingAgent] No method cards found, using LLM fallback")
                return self._llm_select_models(query, df, modeling_intent)
            
            # Convert method cards to model info dicts
            models = []
            for card, score in method_cards:
                model_info = {
                    "name": card.method_name,
                    "score": score,
                    "method_card": card,
                    "python_package": card.python_package,
                    "code_example": card.code_example,
                    "parameters": card.parameters,
                    "data_conditions": card.data_conditions,
                    "typical_use_cases": card.typical_use_cases,
                    "interpretation_guide": card.interpretation_guide,
                    "reasoning": f"Score: {score:.2f} - {card.when_to_use}"
                }
                models.append(model_info)
                print(f"[ModelingAgent]   - {card.method_name} (score: {score:.2f})")
                print(f"[ModelingAgent]     {card.when_to_use[:100]}...")
            
            # LLM ranks and selects best model
            final_selection = self._llm_rank_models(models, query, modeling_intent, data_profile)
            return final_selection
            
        except Exception as e:
            print(f"[ModelingAgent] RAG retrieval error: {e}")
            print(traceback.format_exc())
            return self._llm_select_models(query, df, modeling_intent)
    
    def _llm_rank_models(
        self,
        candidates: List[Dict[str, Any]],
        query: str,
        modeling_intent: Dict[str, Any],
        data_profile: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Use LLM to rank and select best model from RAG candidates.
        
        Args:
            candidates: List of candidate models from RAG
            query: User query
            modeling_intent: Modeling intent
            data_profile: Data profile
            
        Returns:
            Ranked list of models
        """
        # Build candidate summary
        candidate_summary = []
        for i, model in enumerate(candidates):
            card = model.get('method_card')
            summary = f"{i+1}. {model['name']} (score: {model['score']:.2f})\n"
            summary += f"   - {card.when_to_use}\n"
            if card.typical_use_cases:
                summary += f"   - Use cases: {', '.join(card.typical_use_cases[:2])}\n"
            if card.data_conditions:
                conditions = []
                if card.data_conditions.requires_normality:
                    conditions.append("requires normal distribution")
                if card.data_conditions.handles_missing_values:
                    conditions.append("handles missing values")
                if not card.data_conditions.sensitive_to_outliers:
                    conditions.append("robust to outliers")
                if conditions:
                    summary += f"   - Conditions: {', '.join(conditions)}\n"
            candidate_summary.append(summary)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a model selection expert. Given candidate models from RAG retrieval,
select and rank the best models for this problem.

Problem Context:
- Problem type: {problem_type}
- Query: {query}
- Data profile: {data_profile_summary}

Candidate Models:
{candidates}

Select the top 3 models and explain why. Respond in JSON:
{{
    "ranked_models": [
        {{
            "name": "model_name",
            "rank": 1,
            "reasoning": "why this model is best for this problem"
        }}
    ]
}}"""),
            ("user", "Select the best models for this problem.")
        ])
        
        # Build data profile summary
        profile_summary = "Not available"
        if data_profile:
            profile_summary = f"Samples: {data_profile.get('total_rows', 'N/A')}, "
            profile_summary += f"Missing: {data_profile.get('missing_values', {}).get('total_pct', 0):.1f}%, "
            profile_summary += f"Non-normal: {data_profile.get('has_non_normal', False)}, "
            profile_summary += f"Outliers: {data_profile.get('has_outliers', False)}"
        
        response = self.llm.invoke(prompt.format_messages(
            problem_type=modeling_intent.get('problem_type', 'unknown'),
            query=query,
            data_profile_summary=profile_summary,
            candidates="\n".join(candidate_summary)
        ))
        
        # Parse response and reorder candidates
        import json
        try:
            selection = json.loads(response.content)
            ranked = selection.get('ranked_models', [])
            
            # Reorder candidates based on LLM ranking
            ordered_models = []
            for rank_info in ranked:
                model_name = rank_info.get('name')
                for model in candidates:
                    if model['name'] == model_name:
                        model['llm_reasoning'] = rank_info.get('reasoning')
                        ordered_models.append(model)
                        break
            
            # Add any remaining candidates
            for model in candidates:
                if model not in ordered_models:
                    ordered_models.append(model)
            
            return ordered_models if ordered_models else candidates
            
        except Exception as e:
            print(f"[ModelingAgent] LLM ranking failed: {e}, using RAG scores")
            return candidates
    
    def _llm_select_models(
        self,
        query: str,
        df: pd.DataFrame,
        modeling_intent: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fallback: Use LLM to select models without RAG.
        
        Args:
            query: User query
            df: DataFrame
            modeling_intent: Modeling intent
            
        Returns:
            List of model dictionaries
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a model selection expert. Recommend 3 suitable machine learning models
for this problem. Consider:
- Problem type: {problem_type}
- Dataset size: {n_samples} samples, {n_features} features
- Target: {target_column}

Respond in JSON:
{{
    "models": [
        {{
            "name": "ModelName",
            "python_package": "sklearn|statsmodels|scipy",
            "reasoning": "why this model is suitable",
            "code_template": "from ... import ...; model = ..."
        }}
    ]
}}"""),
            ("user", "{query}")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            query=query,
            problem_type=modeling_intent.get('problem_type', 'classification'),
            n_samples=len(df),
            n_features=len(modeling_intent.get('feature_columns', [])),
            target_column=modeling_intent.get('target_column', 'target')
        ))
        
        import json
        try:
            result = json.loads(response.content)
            models = []
            for m in result.get('models', []):
                models.append({
                    "name": m.get('name', 'Unknown'),
                    "score": 1.0,
                    "python_package": m.get('python_package', 'sklearn'),
                    "reasoning": m.get('reasoning', ''),
                    "code_example": m.get('code_template', '')
                })
            return models
        except:
            # Ultimate fallback
            return [{
                "name": "RandomForestClassifier",
                "score": 1.0,
                "python_package": "sklearn",
                "reasoning": "Fallback default model",
                "code_example": "from sklearn.ensemble import RandomForestClassifier"
            }]
    
    def _generate_training_code(
        self,
        model_info: Dict[str, Any],
        df: pd.DataFrame,
        modeling_intent: Dict[str, Any],
        query: str
    ) -> str:
        """Generate Python code to train the selected model.
        
        Args:
            model_info: Selected model information
            df: DataFrame
            modeling_intent: Modeling intent
            query: User query
            
        Returns:
            Python code string
        """
        method_card = model_info.get('method_card')
        
        # Build code from method card template if available
        if method_card and method_card.code_example:
            code_template = method_card.code_example
        else:
            code_template = model_info.get('code_example', '')
        
        # Use LLM to generate complete training code
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Python ML engineer. Generate complete training code for this model.

Model: {model_name}
Package: {package}
Problem Type: {problem_type}
Code Template:
{code_template}

Requirements:
1. Use the provided code template as reference
2. Split data into train/test (80/20) using train_test_split
   - For CLASSIFICATION: Use stratify=y ONLY if there are enough samples per class (at least 2)
   - For REGRESSION: Do NOT use stratify parameter at all
3. Train the model on training data
4. Generate predictions on test data
5. Calculate appropriate metrics ({metrics})
6. Include cross-validation (5-fold) with appropriate scoring
7. Extract feature importance if available (for tree-based models)
8. Store results in a dict: {{'model': model, 'predictions': y_pred, 'metrics': {{}}, 'feature_importance': ...}}

IMPORTANT: Assume data is already preprocessed and clean (no missing values, categorical variables already encoded).
The preprocessing agent has already handled missing values and categorical encoding.

Target column: {target}
Feature columns: {features}

Return ONLY executable Python code, no markdown, no explanations."""),
            ("user", "Generate the training code.")
        ])
        
        # Determine metrics based on problem type
        problem_type = modeling_intent.get('problem_type', 'classification')
        if problem_type == 'classification':
            metrics = "accuracy, precision, recall, F1, AUC-ROC"
        else:
            metrics = "MSE, RMSE, MAE, R², Adjusted R²"
        
        response = self.llm.invoke(prompt.format_messages(
            model_name=model_info['name'],
            package=model_info.get('python_package', 'sklearn'),
            problem_type=problem_type,
            code_template=code_template,
            metrics=metrics,
            target=modeling_intent.get('target_column', 'target'),
            features=modeling_intent.get('feature_columns', [])
        ))
        
        # Clean code
        code = response.content
        code = code.replace('```python', '').replace('```', '').strip()
        
        return code
    
    def _regenerate_training_code(
        self,
        model_info: Dict[str, Any],
        df: pd.DataFrame,
        modeling_intent: Dict[str, Any],
        query: str,
        error_message: str,
        failed_code: str
    ) -> str:
        """Regenerate training code after execution failure.
        
        Args:
            model_info: Selected model information
            df: DataFrame
            modeling_intent: Modeling intent info
            query: Original query
            error_message: Error from previous attempt
            failed_code: Code that failed
            
        Returns:
            Regenerated training code
        """
        # Get column info
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a machine learning expert. The previous model training code failed.

Your task: Fix the code based on the error message.

Common issues to fix:
- Categorical variables not encoded (add LabelEncoder or OneHotEncoder)
- Could not convert string to float (check for non-numeric data in features)
- Missing values in data (add imputation)
- Target variable has wrong type
- Column name mismatches

Rules:
- Add categorical encoding if needed (use LabelEncoder for target, OneHotEncoder for features)
- Handle missing values before training
- Verify column names exist
- Ensure target variable is numeric for regression
- Import all required libraries

Return ONLY executable Python code, no explanations."""),
            ("user", """Model: {model_name}
Problem type: {problem_type}
Target variable: {target}

DataFrame info:
- Numeric columns: {numeric_cols}
- Categorical columns: {categorical_cols}
- Shape: {shape}

Failed code:
```python
{failed_code}
```

Error message:
{error}

Fix the code and generate a complete working solution:""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({
            "model_name": model_info.get("name", "unknown"),
            "problem_type": modeling_intent.get("problem_type", "unknown"),
            "target": modeling_intent.get("target_variable", "unknown"),
            "numeric_cols": numeric_cols,
            "categorical_cols": categorical_cols,
            "shape": df.shape,
            "failed_code": failed_code,
            "error": error_message
        })
        
        # Extract code from response
        code = response.content.strip()
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
        
        return code
    
    def _execute_training_code(self, code: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute model training code.
        
        Args:
            code: Python code to execute
            df: DataFrame
            
        Returns:
            Results dict with model, predictions, metrics
        """
        namespace = {
            'df': df,
            'pd': pd,
            'np': np
        }
        
        try:
            exec(code, namespace)
            
            # Extract results
            results = namespace.get('results', {})
            
            # Fallback: try to find common variable names
            if not results:
                results = {
                    'model': namespace.get('model') or namespace.get('clf') or namespace.get('reg'),
                    'predictions': namespace.get('y_pred') or namespace.get('predictions'),
                    'metrics': namespace.get('metrics', {}),
                    'feature_importance': namespace.get('feature_importance')
                }
            
            return results
            
        except Exception as e:
            print(f"[ModelingAgent] Code execution error: {e}")
            print(traceback.format_exc())
            return {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def _interpret_results(self, model_info: Dict[str, Any], training_results: Dict[str, Any]) -> str:
        """Generate interpretation of model results using method card guidance.
        
        Args:
            model_info: Model information
            training_results: Training results
            
        Returns:
            Interpretation text
        """
        method_card = model_info.get('method_card')
        metrics = training_results.get('metrics', {})
        
        interpretation = f"Model: {model_info['name']}\n\n"
        
        # Add method card interpretation guide if available
        if method_card and method_card.interpretation_guide:
            interpretation += f"Interpretation Guide:\n{method_card.interpretation_guide}\n\n"
        
        # Add metrics
        interpretation += "Performance Metrics:\n"
        for metric_name, value in metrics.items():
            interpretation += f"  - {metric_name}: {value}\n"
        
        # Add reasoning
        interpretation += f"\nModel Selection Reasoning:\n{model_info.get('reasoning', 'N/A')}\n"
        
        return interpretation
    
    def _generate_model_summary(
        self,
        model_info: Dict[str, Any],
        training_results: Dict[str, Any],
        modeling_intent: Dict[str, Any]
    ) -> str:
        """Generate formatted model summary output (like statsmodels/sklearn summary).
        
        Args:
            model_info: Model information
            training_results: Training results
            modeling_intent: Modeling intent
            
        Returns:
            Formatted summary string
        """
        summary_lines = []
        
        # Header
        summary_lines.append("=" * 80)
        summary_lines.append(f"MODEL TRAINING SUMMARY")
        summary_lines.append("=" * 80)
        summary_lines.append("")
        
        # Model information
        summary_lines.append(f"Model Type:           {model_info['name']}")
        summary_lines.append(f"Problem Type:         {modeling_intent.get('problem_type', 'N/A')}")
        summary_lines.append(f"Target Variable:      {modeling_intent.get('target_column', 'N/A')}")
        summary_lines.append(f"Number of Features:   {len(modeling_intent.get('feature_columns', []))}")
        summary_lines.append("")
        
        # Selection reasoning
        summary_lines.append("Model Selection Reasoning:")
        summary_lines.append("-" * 80)
        summary_lines.append(f"{model_info.get('reasoning', 'N/A')}")
        summary_lines.append("")
        
        # Performance metrics
        summary_lines.append("Performance Metrics:")
        summary_lines.append("-" * 80)
        metrics = training_results.get('metrics', {})
        if metrics:
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)):
                    summary_lines.append(f"  {metric_name:.<30} {value:.4f}")
                else:
                    summary_lines.append(f"  {metric_name:.<30} {value}")
        else:
            summary_lines.append("  No metrics available")
        summary_lines.append("")
        
        # Feature importance (if available)
        feature_importance = training_results.get('feature_importance')
        if feature_importance:
            summary_lines.append("Feature Importance (Top 10):")
            summary_lines.append("-" * 80)
            if isinstance(feature_importance, dict):
                # Sort by importance
                sorted_features = sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)
                for i, (feature, importance) in enumerate(sorted_features[:10], 1):
                    summary_lines.append(f"  {i:2}. {feature:.<30} {importance:.4f}")
            elif isinstance(feature_importance, list):
                for i, item in enumerate(feature_importance[:10], 1):
                    summary_lines.append(f"  {i:2}. {item}")
            summary_lines.append("")
        
        # Model parameters (if available)
        model_obj = training_results.get('model')
        if model_obj and hasattr(model_obj, 'get_params'):
            try:
                params = model_obj.get_params()
                summary_lines.append("Model Parameters:")
                summary_lines.append("-" * 80)
                for param_name, param_value in sorted(params.items()):
                    # Skip complex objects, only show simple params
                    if isinstance(param_value, (int, float, str, bool, type(None))):
                        summary_lines.append(f"  {param_name:.<30} {param_value}")
                summary_lines.append("")
            except:
                pass
        
        # Interpretation guide from method card
        method_card = model_info.get('method_card')
        if method_card and method_card.interpretation_guide:
            summary_lines.append("Interpretation Guide:")
            summary_lines.append("-" * 80)
            # Wrap interpretation guide to 80 chars
            guide_text = method_card.interpretation_guide
            import textwrap
            wrapped = textwrap.fill(guide_text, width=78, initial_indent="  ", subsequent_indent="  ")
            summary_lines.append(wrapped)
            summary_lines.append("")
        
        # Footer
        summary_lines.append("=" * 80)
        
        return "\n".join(summary_lines)
