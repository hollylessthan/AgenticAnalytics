# Agentic Analytics Architecture

## Overview

**Agentic Analytics** is a multi-agent orchestration framework built with LangGraph and LangChain. The core framework decomposes complex data analysis tasks into specialized agent workflows that collaborate to provide comprehensive insights.

**Data Copilot** is a reference implementation that provides a Streamlit UI on top of Agentic Analytics, demonstrating how the framework can be deployed as an interactive chat interface.

This document describes the **Agentic Analytics core architecture**. The UI layer (Data Copilot) is thin and primarily handles user interaction while delegating all analytical work to the core framework.

## System Design

### Architectural Layers

```
┌─────────────────────────────────────────────────────┐
│           Data Copilot (UI Layer)                   │
│       Streamlit Chat Interface                      │
│   (User input, visualization display, chat hist)    │
└──────────────────┬──────────────────────────────────┘
                   │ (Delegates analytical work)
                   ▼
┌─────────────────────────────────────────────────────┐
│    Agentic Analytics (Core Framework)               │
│        Agent Orchestrator (LangGraph)               │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │  1. Query Classification (Hybrid Router)    │    │
│  │     ├─ Regex Rules (Fast)                   │    │
│  │     ├─ Keyword Matching (Medium)            │    │
│  │     └─ LLM Classification (Accurate)        │    │
│  └─────────────────────────────────────────────┘    │
│                   │                                 │
│                   ▼                                 │
│  ┌─────────────────────────────────────────────┐    │
│  │  2. Agent Selection & Routing               │    │
│  │     ├─ SQL Agent                            │    │
│  │     ├─ Profiling Agent                      │    │
│  │     ├─ Preprocessing Agent                  │    │
│  │     ├─ Modeling Agent                       │    │
│  │     ├─ Analysis Agent                       │    │
│  │     ├─ Visualization Agent                  │    │
│  │     └─ Communication Agent                  │    │
│  └─────────────────────────────────────────────┘    │
│                   │                                 │
│                   ▼                                 │
│  ┌─────────────────────────────────────────────┐    │
│  │  3. Agent Execution & Result Aggregation    │    │
│  │     ├─ Context passing                      │    │
│  │     ├─ Streaming callbacks                  │    │
│  │     ├─ Error-aware retry                    │    │
│  │     └─ Error handling                       │    │
│  └─────────────────────────────────────────────┘    │
└──────────────┬──────────────────────────────────────┘
               │
   ┌───────────┼───────────┬────────────────┐
   │           │           │                │
   ▼           ▼           ▼                ▼
┌──────────┐ ┌──────────┐ ┌─────────┐ ┌─────────────┐
│  RAG     │ │Database  │ │LLM      │ │Cache        │
│System    │ │Manager   │ │Factory  │ │Manager      │
├──────────┤ ├──────────┤ ├─────────┤ ├─────────────┤
│-Schema   │ │-Schema   │ │-OpenAI  │ │-Query       │
│ Context  │ │-Queries  │ │-Claude  │ │ Results     │
│-Method   │ │-Metadata │ │-Google  │ │-Policies    │
│ Cards    │ │-Pooling  │ │-Bedrock │ │-Concurrency │
└──────────┘ └──────────┘ └─────────┘ └─────────────┘
   │           │
   │           ▼
   │       ┌──────────────────────────────┐
   │       │    Target Databases          │
   │       │ ├─ PostgreSQL                │
   │       │ ├─ MySQL                     │
   │       │ ├─ DuckDB                    │
   │       │ ├─ Snowflake                 │
   │       │ └─ BigQuery                  │
   │       └──────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│    Vector Stores (LanceDB / FAISS / Weaviate)        │
│  - Database schema embeddings                        │
│  - Method cards (40+ ML/stats algorithms)            │
│  - Query example embeddings                          │
│  - Best practice documentation                       │
└──────────────────────────────────────────────────────┘
```

## Agent Orchestrator

The **Agent Orchestrator** (`src/agents/orchestrator.py`) is the core of Agentic Analytics. It coordinates specialized agents using a state machine pattern with LangGraph.

### Orchestrator Flow

```
Input Query
    ↓
┌─────────────────────────────────┐
│ STATE: Initialize               │
│ - Store query                   │
│ - Fetch conversation context    │
│ - Load RAG schema info          │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ STATE: Classify Query           │
│ - Run hybrid router             │
│ - Determine plan type           │
│ - Select appropriate agent(s)   │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ STATE: Execute Agents           │
│ ├─ SQL Agent (if needed)        │
│ │  ├─ Retrieve schema context   │
│ │  ├─ Generate SQL              │
│ │  └─ Execute & limit results   │
│ │                               │
│ ├─ Profiling Agent (if needed)  │
│ │  ├─ Generate data profile     │
│ │  ├─ Quality assessment        │
│ │  └─ RAG test suggestions      │
│ │                               │
│ ├─ Preprocessing Agent (opt)    │
│ │  ├─ RAG recommendations       │
│ │  ├─ User confirmation         │
│ │  ├─ Apply transformations     │
│ │  └─ Error-aware retry         │
│ │                               │
│ ├─ Modeling Agent (optional)    │
│ │  ├─ Intent detection          │
│ │  ├─ RAG model selection       │
│ │  ├─ Train model               │
│ │  └─ Error-aware retry         │
│ │                               │
│ ├─ Analysis Agent (if needed)   │
│ │  ├─ Compute statistics        │
│ │  ├─ Detect trends             │
│ │  └─ Generate insights         │
│ │                               │
│ ├─ Visualization Agent (opt)    │
│ │  ├─ Select chart type         │
│ │  ├─ Create visualization      │
│ │  └─ Format for display        │
│ │                               │
│ └─ Communication Agent          │
│    ├─ Format response           │
│    ├─ Add context               │
│    ├─ Handle confirmations      │
│    └─ Prepare for streaming     │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ STATE: Cache Results            │
│ - Evaluate caching eligibility  │
│ - Store if eligible             │
│ - Return to user                │
└─────────────────────────────────┘
    ↓
Output with inline visualizations
```

### State Management

The orchestrator maintains state throughout execution:

```python
class AgentState(BaseModel):
    """State passed between agents."""
    query: str                                 # Original user query
    plan_type: Optional[str]                   # Execution plan (SQL_ONLY, SQL_MODELING, etc)
    confidence_score: Optional[float]          # Classifier confidence
    agent_chain: List[str]                     # Sequence of agents executed
    
    # SQL outputs
    sql_query: Optional[str]                   # Generated SQL
    query_results: Optional[Any]               # Query execution results
    
    # Profiling outputs
    data_profile: Optional[Dict[str, Any]]     # Comprehensive data profile
    data_summary: Optional[Dict[str, Any]]     # Quick quality summary
    
    # Preprocessing outputs
    preprocessing_needed: Optional[Dict]       # Recommended transformations
    preprocessing_approved: List[str]          # User-approved steps
    preprocessing_applied: Optional[Dict]      # Applied transformations
    preprocessed_dataframe: Optional[Any]      # Preprocessed data
    preprocessing_code: Optional[str]          # Generated preprocessing code
    needs_preprocessing_confirmation: bool     # Pause for user approval
    
    # Modeling outputs
    model_results: Optional[Dict[str, Any]]    # Training results & metrics
    model_summary: Optional[str]               # Formatted model summary
    modeling_code: Optional[str]               # Generated training code
    
    # Analysis outputs
    analysis_code: Optional[str]               # Generated analysis code
    analysis_results: Optional[str]            # Analysis findings
    
    # Visualization outputs
    visualization_code: Optional[str]          # Visualization code
    visualization_path: Optional[str]          # Chart file path
    
    # Communication outputs
    final_response: Optional[str]              # Main response to user
    final_answer: Optional[str]                # Backward compatibility
    
    # Session state
    cached_dataframe: Optional[Any]            # Cached data from previous query
    state_history: List[ConversationSnapshot]  # Multi-turn context
    
    # Error handling
    errors: List[str]                          # Error messages
    metadata: Dict[str, Any]                   # Additional context
```

## Query Classifier (Hybrid Router)

The **Query Classifier** (`src/agents/query_classifier.py`) uses a 3-tier approach to determine optimal execution plans:

### Plan Types

```python
class PlanType(Enum):
    SQL_ONLY = "sql_only"                    # Simple SQL query
    SQL_ANALYSIS = "sql_analysis"            # SQL + statistical analysis
    SQL_VIZ = "sql_viz"                      # SQL + visualization
    SQL_ANALYSIS_VIZ = "sql_analysis_viz"    # SQL + analysis + viz
    SQL_PROFILING = "sql_profiling"          # SQL + data profiling
    SQL_PREPROCESSING = "sql_preprocessing"  # SQL + profile + preprocess
    SQL_MODELING = "sql_modeling"            # Full ML pipeline
```

### Tier 1: Regex Rules (Fast)

Fast pattern matching for common simple queries:

```
Pattern Examples:
- "show", "get", "list" → SQL_ONLY
- "visualize", "plot", "chart" → SQL_VIZ
- "profile", "explore", "EDA" → SQL_PROFILING
- "model", "predict", "classify" → SQL_MODELING
```

**Performance**: ~2ms  
**Coverage**: ~40% of typical queries

### Tier 2: Keyword Matching (Medium)

Keyword-based classification for known query patterns:

```
Keywords:
- "preprocessing", "feature engineering" → SQL_PREPROCESSING
- "train", "build model", "machine learning" → SQL_MODELING
- "data quality", "missing values" → SQL_PROFILING
- "top", "highest", "trend" → SQL_ANALYSIS
```

**Performance**: ~5ms  
**Coverage**: ~50% of queries

### Tier 3: LLM Classification (Accurate)

For complex queries needing semantic understanding:

```
Uses LLM to understand:
- Business logic and context
- Complex joins needed
- Advanced analysis required
- Custom aggregations
```

**Performance**: ~80ms  
**Coverage**: ~10% of queries (but most critical)

### Router Decision Logic

```python
def classify_query(query: str) -> QueryType:
    # Try fast regex patterns first
    if matches_simple_pattern(query):
        return QueryType.SIMPLE_SELECT  # 2ms
    
    # Try keyword matching
    if has_aggregation_keywords(query):
        return QueryType.AGGREGATION    # 5ms
    
    # Fall back to LLM
    return llm_classify(query)          # 80ms
```

## Specialized Agents

### SQL Agent

**Purpose**: Translate natural language to SQL queries with intelligence

**Workflow**:
1. Receive user query and schema context
2. Retrieve relevant schema via RAG
3. Identify tables and JOINs needed
4. Generate SQL with parameterized queries
5. Apply row limits and validate
6. Execute on database
7. Return results and execution metadata

**Key Features**:
- **Automatic JOIN Intelligence**: Uses RAG to discover relationships
- **Schema Validation**: Ensures columns/tables exist
- **Query Optimization**: Suggests better queries if needed
- **Row Limiting**: Enforces safety limits
- **Error Recovery**: Handles invalid queries gracefully

**Example**:
```
User: "Show me top 10 customers by revenue"
    ↓
SQL Agent:
  1. Schema retrieval: Found customers, orders tables
  2. JOIN detection: orders has customer_id foreign key
  3. SQL generation: SELECT c.id, c.name, SUM(o.amount) ...
  4. Execution: Query with LIMIT 10 applied
  5. Results: DataFrame with results
```

### Analysis Agent

**Purpose**: Derive insights and statistics from data

**Capabilities**:
- **Descriptive Statistics**: Mean, median, std dev, quantiles
- **Trend Analysis**: Growth rates, momentum
- **Anomaly Detection**: Outlier identification
- **Correlation Analysis**: Relationships between variables
- **Business Insights**: Context-aware interpretation

**Example**:
```
Input: Sales data for 12 months
    ↓
Analysis:
  - Mean monthly sales: $150K
  - Trend: +5% month-over-month
  - Anomaly: October spike (+25%)
  - Insight: Seasonal pattern detected
```

### Visualization Agent

**Purpose**: Create appropriate visual representations

**Capabilities**:
- **Chart Type Selection**: Auto-selects best chart type
- **Interactive Plots**: Plotly-based interactive visualizations
- **Table Formatting**: Responsive, readable tables
- **Color Schemes**: Theme-aware color palettes
- **Mobile Responsive**: Displays well on all devices

**Chart Selection Logic**:
```
1 numeric column     → Histogram/Distribution
2 numeric columns   → Scatter/Line chart
1 categorical, 1 numeric → Bar/Column chart
Time series data     → Line chart with trend
Multiple categories  → Grouped bar chart
Proportions         → Pie/Donut chart
```

### Profiling Agent

**Purpose**: Generate comprehensive data quality profiles

**Capabilities**:
- **Data Quality Assessment**: Missing values, duplicates, outliers
- **Statistical Analysis**: Distribution analysis, normality tests
- **Type Detection**: Automatic column type identification
- **Correlation Analysis**: Relationship detection between features
- **RAG-Powered Test Suggestions**: Recommends appropriate statistical tests

**Workflow**:
```
Input: DataFrame
    ↓
Profile Generation:
  - Shape analysis (rows, columns)
  - Missing value detection
  - Duplicate detection
  - Distribution analysis (skewness, kurtosis)
  - Outlier detection (IQR method)
  - Correlation matrix
    ↓
RAG Test Suggestions:
  - Normality tests (Shapiro-Wilk)
  - Group comparison tests (t-test, ANOVA)
  - Regression suitability
    ↓
Output: Comprehensive data profile
```

### Preprocessing Agent

**Purpose**: Transform and prepare data for modeling with error-aware retry

**Capabilities**:
- **RAG-Powered Recommendations**: Uses method cards for intelligent preprocessing
- **Missing Value Handling**: Imputation strategies (mean, median, mode)
- **Categorical Encoding**: Label encoding, one-hot encoding
- **Feature Scaling**: StandardScaler, MinMaxScaler, RobustScaler
- **Distribution Normalization**: Log/power transforms for skewed data
- **Outlier Treatment**: IQR-based detection and handling
- **Error-Aware Retry**: Regenerates code based on execution errors (up to 3 attempts)

**Error Recovery**:
```
Attempt 1: Generate preprocessing code
    ↓ [Execution fails: f-string error]
Attempt 2: Regenerate with simpler variable names
    ↓ [Execution fails: OneHotEncoder sparse parameter]
Attempt 3: Regenerate with updated sklearn API
    ↓
Success: Preprocessed DataFrame
```

**User Confirmation Flow**:
```
Detect preprocessing needed
    ↓
Generate recommendations (RAG-powered)
    ↓
Pause for user approval (if mode = "confirm")
    ↓
User selects transformations
    ↓
Apply selected preprocessing
    ↓
Return preprocessed DataFrame
```

### Modeling Agent

**Purpose**: Train and evaluate machine learning models with error-aware retry

**Capabilities**:
- **Intent Detection**: Identifies regression vs classification problems
- **RAG-Powered Model Selection**: Recommends models from method cards
- **Automated Training**: Generates and executes training code
- **Model Evaluation**: Comprehensive metrics (R², RMSE, MAE, cross-validation)
- **Feature Importance**: Identifies key predictive features
- **Error-Aware Retry**: Fixes code generation errors automatically (up to 3 attempts)

**Error Recovery**:
```
Attempt 1: Generate training code
    ↓ [Execution fails: could not convert string to float 'M']
Attempt 2: Regenerate with categorical encoding
    ↓ [Execution fails: OneHotEncoder API error]
Attempt 3: Regenerate with corrected sklearn API
    ↓
Success: Trained model with metrics
```

**Workflow**:
```
Input: Preprocessed DataFrame
    ↓
Intent Detection:
  - Problem type (regression/classification)
  - Target variable identification
  - Feature selection
    ↓
RAG Model Selection:
  - Query method cards database
  - Rank models by suitability
  - Select top candidate
    ↓
Code Generation & Execution:
  - Generate training code
  - Execute with error recovery
  - Extract metrics and results
    ↓
Output: Model results + formatted summary
```

### Communication Agent

**Purpose**: Format responses for user consumption

**Responsibilities**:
- Compose final response text
- Structure multiple result types
- Add context and explanations
- Prepare for streaming output
- Handle error messaging
- Pause for preprocessing/modeling confirmations

## RAG System

The **RAG System** (`src/rag/rag_system.py`) provides schema context to agents.

### Components

**Vector Store** (`src/rag/vector_store.py`):
- Supports FAISS (in-memory) and Weaviate (persistent)
- Stores embeddings for:
  - Table schemas
  - Column descriptions
  - Example queries
  - Best practices

**Indexing Process**:
```
1. Extract schema metadata
   └─ Table names, columns, types, constraints
2. Create embeddings
   └─ Vector representation of schema
3. Store in vector database
   └─ FAISS or Weaviate
4. Make retrievable
   └─ Semantic search ready
```

**Retrieval Process**:
```
User Query: "Show top 10 customers"
    ↓
Embedding: Vector representation
    ↓
Semantic Search: Find relevant schema
    ↓
Retrieved Context:
  - Table: customers
  - Table: orders
  - Relationship: customers.id = orders.customer_id
  - Column relevance scores
    ↓
Passed to SQL Agent
```

## Method Knowledge Base

Agentic Analytics includes a **curated knowledge base of 40+ statistical tests, ML algorithms, preprocessing techniques, and evaluation metrics**. Each method is represented as a structured "method card" that enables intelligent, data-aware recommendations.

### Method Card System

**Method cards** replace traditional documentation chunking with structured knowledge units that contain:

- **Decision Criteria**: When to use vs when not to use
- **Data Requirements**: Sample size, normality, missing values, multicollinearity constraints
- **Implementation Details**: Code examples, parameters, library support (scikit-learn, scipy, statsmodels)
- **Interpretation Guides**: How to read results, statistical significance, practical implications
- **Typical Use Cases**: Real-world scenarios and applications

### Coverage

**Machine Learning Models**:
- Classification: Logistic Regression, Random Forest, SVM, Gradient Boosting
- Regression: OLS, Ridge (L2), Lasso (L1), Elastic Net, GLS (heteroscedasticity)

**Statistical Tests**:
- Normality: Shapiro-Wilk, Anderson-Darling, Kolmogorov-Smirnov
- Group Comparison: t-tests (independent/paired), ANOVA, Kruskal-Wallis, Mann-Whitney
- Correlation: Pearson, Spearman, Kendall
- Categorical: Chi-Square, Fisher's Exact

**Preprocessing Methods**:
- Imputation: SimpleImputer (mean/median/mode), KNN Imputer, Iterative Imputer
- Scaling: StandardScaler, MinMaxScaler, RobustScaler
- Encoding: Label Encoding, One-Hot Encoding

**Evaluation Metrics**:
- Regression: MSE, RMSE, MAE, R², Adjusted R²
- Classification: Accuracy, Precision, Recall, F1, AUC-ROC

### Intelligent Retrieval

Method cards are indexed in **LanceDB** (vector store) and retrieved using **RAG-powered semantic search** combined with **constraint-based filtering**:

```
User Query: "impute missing values in dataset with outliers"
    ↓
Data Profile:
  - 100 samples
  - 15% missing values
  - Outliers detected in 3 columns
  - Non-normal distribution
    ↓
RAG Retrieval:
  1. Semantic search: "impute missing outliers"
  2. Filter by constraints:
     - sample_size_min ≤ 100 ≤ sample_size_max
     - handles_missing_values = true
     - handles_outliers = true
    ↓
Top Results:
  1. SimpleImputer (median) - robust to outliers
  2. RobustScaler - for later scaling
  3. KNNImputer - alternative approach
    ↓
Return to Preprocessing Agent
```

### Integration with Agents

**Profiling Agent**:
- Suggests statistical tests based on data characteristics
- Recommends correlation methods (Pearson vs Spearman) based on normality

**Preprocessing Agent**:
- Retrieves imputation methods matched to data profile
- Selects scaling/encoding techniques appropriate for modeling intent

**Modeling Agent**:
- Recommends models based on problem type (classification/regression)
- Filters models by data constraints (sample size, features, multicollinearity)
- Uses interpretation guides to explain model results

### Method Card Loading

Method cards are loaded from YAML files in `method_cards/` directory:

```bash
# Load method cards into LanceDB
python testing/load_method_cards.py

# Test retrieval
python testing/test_method_card_retrieval.py
```

See [METHOD_CARDS.md](METHOD_CARDS.md) for complete documentation and [method_cards/README.md](../method_cards/README.md) for card structure.

## Human-in-the-Loop Architecture

Agentic Analytics incorporates **Human-in-the-Loop (HITL)** capabilities for critical decision points, ensuring user control over data transformations and model training:

### Preprocessing Confirmation

When data preprocessing is recommended, the system **pauses execution** and presents recommendations to the user:

```
Query: "Build a model to predict customer lifetime value"
    ↓
Profiling Agent: Detects data quality issues
    ↓
Preprocessing Agent: Generates recommendations
    ↓
PAUSE: Show user preprocessing dialog
    ├─ Encode categorical variables
    ├─ Fill missing values
    ├─ Scale features
    ├─ Transform skewed distributions
    └─ Handle outliers
    ↓
User selects desired transformations
    ↓
Apply selected preprocessing
    ↓
Continue to modeling
```

**Modes**:
- **Confirm** (default): Pause and ask user approval
- **Auto**: Apply all recommendations automatically
- **Manual**: Skip preprocessing unless explicitly requested

### Benefits of HITL

1. **Transparency**: Users see exactly what transformations are applied
2. **Control**: Users can exclude transformations they don't want
3. **Trust**: Builds confidence in the ML pipeline
4. **Learning**: Users understand data quality issues
5. **Compliance**: Meets regulatory requirements for human oversight

### Implementation

The Communication Agent detects `needs_preprocessing_confirmation` and sets `final_response = None`, signaling the UI to display the confirmation dialog instead of a text response. The orchestrator resumes execution after user approval.

## Security Architecture

### SQL Injection Prevention

- **Parameterized Queries**: All user input via parameters
- **Query Validation**: Schema validation before execution
- **Statement Parsing**: AST analysis of generated SQL
- **Keyword Filtering**: Dangerous operations blocked

### Row Limiting

- **Configurable Limits**: Default 1,000 rows
- **LIMIT Enforcement**: Added to all queries
- **Intelligent Caching**: Large results not cached
- **User Visibility**: Informs users of limits

### DataFrame Safety

- **Type Validation**: Ensures safe operations
- **Column Checking**: Validates column existence
- **Safe Operations**: Whitelist of allowed pandas operations
- **Error Handling**: Graceful degradation

### Concurrent Access Control

- **Connection Pooling**: Limits simultaneous connections
- **Queue Management**: Manages concurrent requests
- **Timeout Handling**: Prevents hanging queries
- **Resource Cleanup**: Proper cleanup on completion

## Memory & Session Management

### Conversation Memory

- **Short-term**: Last 10 turns in current session
- **Context Sliding Window**: Maintains relevant context
- **Snapshot History**: Save/restore conversation states
- **Rollback Capability**: Revert to previous snapshots

### Session Storage

```
Session Data:
├── Conversation history
├── User preferences
├── Query history with results
├── Cached analysis results
├── Schema snapshots
└── Performance metrics
```

## Caching Strategy

### Cache Eligibility

Results cached if:
- Query results < row limit
- Query is deterministic (no RANDOM, NOW, etc)
- Database hasn't changed (schema validation)
- Not already cached

Results NOT cached if:
- Results > row limit
- Contains volatile functions
- User explicitly disables
- Real-time data required

### Cache Operations

```
Query Execution:
1. Check cache key (normalized query)
2. If hit: Return cached result
3. If miss:
   a. Execute query
   b. Evaluate caching eligibility
   c. Store if eligible
   d. Return result
```

## Streaming Architecture

Real-time visibility into agent reasoning:

### Callback System

```python
class StreamingCallback:
    def on_agent_start(self, tool, input):
        """Called when agent starts"""
        
    def on_agent_end(self, output):
        """Called when agent completes"""
        
    def on_tool_start(self, tool_input):
        """Called when tool starts"""
        
    def on_tool_end(self, output):
        """Called when tool completes"""
```

### User Experience

```
User: "Show top 5 products"
    ↓
[Streaming] Classifying query... SQL Query
[Streaming] Retrieving schema context...
[Streaming] Generating SQL...
    Generated: SELECT product_id, SUM(quantity) ...
[Streaming] Executing query...
[Streaming] Creating visualization...
[Streaming] Formatting response...
    ↓
Final Result with inline chart
```

## Configuration & Extensibility

### Adding New Agents

1. **Inherit from BaseAgent**:
```python
from agents.base import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__("custom", "Description")
        self.llm = llm
    
    def execute(self, state: OrchestrationState) -> OrchestrationState:
        # Your logic here
        return state
```

2. **Register in Orchestrator**:
```python
self.agents = {
    "custom": CustomAgent(self.llm),
    # ... other agents
}
```

3. **Update Router Logic**:
```python
if query_type == "custom_type":
    return self.agents["custom"].execute(state)
```

### Adding New Vector Stores

Implement the `VectorStoreBase` interface and register in factory:

```python
class CustomVectorStore(VectorStoreBase):
    def index(self, documents):
        # Index documents
        
    def search(self, query, k=5):
        # Return top-k results
```

## Performance Optimization

### Query Caching

Results cached at multiple levels:
- LLM response caching (same SQL generated)
- Query result caching (identical queries)
- Embedding caching (schema embeddings)

### Lazy Loading

- Schema loaded on demand
- RAG index lazy initialized
- Database connections pooled
- LLM calls cached when possible

### Parallelization

- Multiple agents can run in parallel if independent
- Vector search parallelized across dimensions
- Visualization generation async

## Error Handling & Recovery

### Error Hierarchy

```
OrchestrationError (base)
├── QueryClassificationError
├── SQLGenerationError
├── QueryExecutionError
├── AnalysisError
├── VisualizationError
└── CommunicationError
```

### Recovery Strategies

```
SQL Error:
  1. Try simplified query
  2. Retrieve schema again
  3. Regenerate with constraints
  4. Return helpful error message

LLM Error:
  1. Retry with different prompt
  2. Fall back to simpler approach
  3. Return cached result if available
  4. Inform user of limitation

Database Error:
  1. Check connection
  2. Retry with backoff
  3. Fall back to cache
  4. Report to user
```

## Monitoring & Observability

### Metrics Collected

- Query classification type distribution
- Agent execution times
- Query performance (from database)
- Cache hit/miss rates
- Error rates and types
- User interaction patterns

### Logging

- Query execution logs
- Agent step logs
- Cache operations
- Error logs with full context
- Performance metrics

## Deployment Considerations

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN pip install -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "src/app.py"]
```

### Scaling Strategies

- **Horizontal**: Multiple app instances behind load balancer
- **Vertical**: Larger machine for database/cache
- **Vector Store**: Managed Weaviate for large-scale
- **Database**: Connection pooling and read replicas

---

See [HYBRID_ROUTING_IMPLEMENTATION.md](HYBRID_ROUTING_IMPLEMENTATION.md) for query routing details and [SQL_SECURITY.md](SQL_SECURITY.md) for security implementation.
