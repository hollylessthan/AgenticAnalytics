# RAG System Documentation

## Overview

The Retrieval-Augmented Generation (RAG) system in Agentic Analytics enables intelligent method selection by embedding statistical/ML method knowledge into the agents. This system uses LanceDB vector store to retrieve relevant method cards based on data characteristics and user queries.

## Architecture

### Components

1. **Method Cards** (`method_cards/*.yaml`)
   - YAML files containing metadata for statistical methods, ML models, preprocessing techniques
   - Each card includes: name, description, constraints, code examples, interpretation guides

2. **RAG System** (`src/rag/rag_system.py`)
   - Manages vector embeddings and retrieval
   - Provides specialized retrieval methods for different agent types
   - Uses LanceDB for persistent vector storage

3. **Integration Points**
   - **ModelingAgent**: RAG-powered model selection
   - **PreprocessingAgent**: RAG-guided data transformation
   - **ProfilingAgent**: RAG-suggested statistical tests
   - **AnalysisAgent**: RAG-selected analysis methods
   - **CommunicationAgent**: RAG-enhanced metric interpretation

## Method Card Structure

```yaml
category: "classification_models"
name: "Random Forest Classifier"
description: "Ensemble learning method using decision trees"
method_class: "RandomForestClassifier"
library: "scikit-learn"
constraints:
  - handles_missing_values: false
  - requires_normality: false
  - sensitive_to_outliers: false
  - min_samples: 100
  - max_samples: 100000
typical_use_cases:
  - "Binary or multi-class classification"
  - "Feature importance analysis"
code_example: |
  from sklearn.ensemble import RandomForestClassifier
  clf = RandomForestClassifier(n_estimators=100, random_state=42)
  clf.fit(X_train, y_train)
  predictions = clf.predict(X_test)
interpretation_guide: |
  - Feature importance shows relative importance of each feature
  - Higher Out-of-bag score indicates better generalization
sources:
  - "https://scikit-learn.org/stable/modules/ensemble.html"
```

## RAG-Enhanced Agent Workflows

### 1. ModelingAgent

**Flow**:
```
Query: "Build a model to predict customer churn"
  ↓
Data Profile: {has_non_normal: true, outliers: true, rows: 1000}
  ↓
RAG Query: "binary classification model 1000 samples non-normal distribution"
  ↓
Retrieved: RandomForestClassifier (score: 0.92), LogisticRegression (score: 0.65)
  ↓
LLM Ranks: RandomForestClassifier (handles non-normal data, robust to outliers)
  ↓
Code Generation: Uses method card code_example as template
  ↓
Training: Executes code, returns metrics
  ↓
Interpretation: Uses method card interpretation_guide
```

**Key Methods**:
- `_rag_select_models()`: Retrieves candidate models from vector store
- `_llm_rank_models()`: Uses LLM to rank and explain selection
- `_generate_training_code()`: Generates code using method card templates

### 2. PreprocessingAgent

**Flow**:
```
Data Issues: 5% missing values, outliers detected, categorical features
  ↓
RAG Queries:
  - "impute missing values numerical robust outliers" → SimpleImputer (median)
  - "encode categorical features" → OneHotEncoder
  - "scale features robust outliers" → RobustScaler
  ↓
Generates unified preprocessing pipeline
  ↓
User confirms transformations
  ↓
Applies preprocessing with error-aware retry (fixes f-string errors, type mismatches)
```

**Key Methods**:
- `_rag_select_preprocessing_methods()`: Retrieves preprocessing method cards
- `_generate_preprocessing_code()`: Creates preprocessing pipeline
- `_regenerate_preprocessing_code()`: Fixes errors on retry (NEW: error-aware retry)

### 3. ProfilingAgent

**Flow**:
```
Data Profile Generated: types, distributions, missing values, outliers
  ↓
RAG Suggests Tests:
  - Non-normal → Shapiro-Wilk Test
  - Correlation → Spearman (non-parametric)
  - Group comparison → Mann-Whitney or Kruskal-Wallis
  ↓
Stores suggestions in data_profile['suggested_tests']
```

**Key Methods**:
- `_suggest_statistical_tests()`: RAG-powered test recommendations
- Uses `retrieve_methods_for_statistics()` with data characteristics

### 4. AnalysisAgent

**Flow**:
```
Query: "Calculate correlation between sales and marketing spend"
  ↓
Data Profile: Non-normal distribution
  ↓
RAG Query: "correlation test non-normal spearman"
  ↓
Retrieved: Spearman Correlation (score: 0.94)
  ↓
Code Generation: Uses scipy.stats.spearmanr
  ↓
Results: Correlation coefficient with p-value interpretation
```

**Key Methods**:
- `_rag_select_analysis_methods()`: Retrieves statistical analysis methods
- `_generate_analysis_code()`: Creates analysis code with error-aware retry (NEW)
- `_regenerate_analysis_code()`: Fixes f-string errors and type mismatches (NEW)

### 5. CommunicationAgent

**Flow**:
```
Model Results: {accuracy: 0.85, auc_roc: 0.88, f1: 0.82}
  ↓
RAG Interprets Each Metric:
  - Accuracy 0.85 → "Correctly predicts 85% of cases"
  - AUC-ROC 0.88 → "Excellent discrimination ability (>0.8 is very good)"
  - F1 0.82 → "Strong balance between precision and recall"
  ↓
Synthesized Response with interpretations and sources
```

**Key Methods**:
- `_rag_interpret_metrics()`: Retrieves metric interpretation guides
- `_summarize_model_results()`: Formats model output with context

## Error-Aware Retry System (NEW)

All code-generating agents now implement intelligent retry with error-based code regeneration:

### Common Errors Fixed Automatically:
1. **F-string variable name errors**: `{profile.x}` → use simple variables
2. **OneHotEncoder sparse parameter**: `sparse=False` → `sparse_output=False` (sklearn 1.2+)
3. **Type conversion errors**: Add categorical encoding automatically
4. **Missing values in model training**: Add imputation step

### Implementation:
```python
for attempt in range(max_code_retries):  # max 3 attempts
    if attempt == 0:
        code = generate_fresh_code()
    else:
        code = regenerate_code_based_on_error(error_msg, failed_code)
    
    results = execute_code()
    if no_error:
        break
```

### Agents with Error-Aware Retry:
- ✅ AnalysisAgent: `_regenerate_analysis_code()`
- ✅ PreprocessingAgent: `_regenerate_preprocessing_code()`
- ✅ ModelingAgent: `_regenerate_training_code()`
- ✅ ProfilingAgent: Uses direct statistical computation (no code gen)

## Method Card Coverage

Current knowledge base (41 method cards):

| Category | Methods | Count |
|----------|---------|-------|
| Imputation | SimpleImputer (mean, median, mode) | 3 |
| Encoding | OneHotEncoder, LabelEncoder, OrdinalEncoder | 3 |
| Scaling | StandardScaler, MinMaxScaler, RobustScaler | 3 |
| Normality Tests | Shapiro-Wilk, Kolmogorov-Smirnov | 2 |
| Correlation | Pearson, Spearman, Kendall | 3 |
| Classification | RandomForest, LogisticRegression | 2 |
| Regression | OLS, Ridge, Lasso, ElasticNet, GLS, Logistic | 6 |
| Group Comparison | ANOVA, t-tests, Kruskal-Wallis, Mann-Whitney, Chi-square, Binomial | 9 |
| Evaluation Metrics | MSE, RMSE, MAE, R², Adj R², AUC-ROC, Precision, Recall, F1, P-value | 10 |

## Benefits

1. **Intelligent Selection**: Methods chosen based on data characteristics (normality, outliers, sample size)
2. **Best Practices**: Embedded knowledge from scikit-learn, scipy, statsmodels documentation
3. **Consistency**: All agents use same RAG system for coordinated method selection
4. **Interpretability**: Metric interpretations and reasoning provided automatically
5. **Extensibility**: Add new methods by creating YAML cards, no code changes needed
6. **Error Recovery**: Automatic code regeneration fixes common errors (NEW)

## Testing

### Method Card Retrieval Testing

Run comprehensive tests to validate method card retrieval:

```bash
python testing/test_method_card_retrieval.py
```

This test suite validates:
- Basic method card retrieval without data profile
- Constraint-based retrieval with sample size, missing values, normality
- Data-aware recommendations based on data characteristics
- Multi-category retrieval (preprocessing, statistics, modeling)

**Test scenarios include:**
- Small sample classification (< 100 samples) → Suggests Logistic Regression
- Large sample regression (> 10,000 samples) → Suggests Random Forest
- Non-normal data → Suggests Spearman over Pearson correlation
- Missing values → Suggests appropriate imputation methods

See [`testing/test_method_card_retrieval.py`](../testing/test_method_card_retrieval.py) for detailed test cases.

### End-to-End Testing

Test the RAG system with modeling queries:

```python
from src.agents import AgentOrchestrator
from src.config import Config

orchestrator = AgentOrchestrator(Config())

# Will trigger: SQL → Profile → Preprocessing (with confirmation) → Modeling
query = "Build a model to predict customer lifetime value using store sales and demographics"

result = orchestrator.run(query)
# Expected: RAG selects RandomForest, generates code, trains model, interprets results
```

## Extending the System

### Adding New Method Cards

1. Create YAML file in `method_cards/` folder
2. Follow the method card structure template
3. Run `python testing/load_method_cards.py` to rebuild vector index
4. RAG system automatically incorporates new methods

### Example: Adding XGBoost

```yaml
category: "classification_models"
name: "XGBoost Classifier"
description: "Gradient boosting framework with regularization"
method_class: "XGBClassifier"
library: "xgboost"
constraints:
  - handles_missing_values: true
  - requires_normality: false
  - sensitive_to_outliers: false
  - min_samples: 100
  - max_samples: 1000000
typical_use_cases:
  - "Structured/tabular data classification"
  - "Competition-winning model"
  - "Feature importance with SHAP"
code_example: |
  from xgboost import XGBClassifier
  clf = XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1)
  clf.fit(X_train, y_train)
  predictions = clf.predict(X_test)
interpretation_guide: |
  - Feature importance based on gain, cover, or frequency
  - Learning curves help diagnose overfitting
  - SHAP values provide instance-level explanations
sources:
  - "https://xgboost.readthedocs.io/"
```

## Architecture Integration

The RAG system integrates with the orchestrator's hybrid routing:

```
Query Classifier (Tier 1-3)
  ↓
Plan Type: SQL_MODELING
  ↓
SQL Agent → Profiling Agent → Preprocessing Agent → Modeling Agent
               ↓                     ↓                    ↓
           RAG suggests         RAG selects         RAG selects
           tests                preprocessing       model
                                methods
```

All RAG operations are logged for debugging and visibility.
