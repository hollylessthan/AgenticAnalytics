# Method Knowledge Base Guide

## Overview

The **Method Knowledge Base** is a curated collection of structured "method cards" that replace traditional RAG document chunking. Instead of retrieving random documentation paragraphs, the system retrieves **decision units** - structured methods with explicit constraints, assumptions, and usage guidance.

### Why Method Cards?

**Traditional RAG (Document Chunking)**:
- ❌ Random 800-char chunks from documentation
- ❌ No decision criteria
- ❌ Hard to filter by data characteristics
- ❌ Retrieves "how" before "what/when"

**Method Cards**:
- ✅ Curated decision units (30-60 methods)
- ✅ Explicit constraints and requirements
- ✅ Data-aware retrieval (sample size, normality, missing values)
- ✅ Retrieves "what method to use" based on data profile
- ✅ Includes code examples and attributions

---

## Quick Start

### 1. Load Method Cards (First Time Setup)

```bash
# Activate your environment
source venv/bin/activate  # or your virtualenv

# Load method cards into LanceDB
python testing/load_method_cards.py
```

**Output**:
```
🚀 METHOD CARD LOADER
============================================================
📚 Found 5 YAML files
📂 Loading cards from: classification_models.yaml
  ✓ LogisticRegression (model_classification)
  ✓ RandomForestClassifier (model_classification)
  ...
✅ Successfully stored 16 method cards
📍 Location: ./lancedb/method_cards.lance
```

### 2. Use in Your Code

```python
from src.rag.rag_system import RAGSystem

rag = RAGSystem()

# Basic retrieval (no data profile)
methods = rag.retrieve_method_cards(
    query="binary classification model",
    k=3
)

for card, confidence in methods:
    print(f"Method: {card.method_name}")
    print(f"When to use: {card.when_to_use}")
    print(f"Code: {card.code_example}")
```

### 3. Constraint-Based Retrieval (Recommended)

```python
# Provide data profile for constraint matching
data_profile = {
    "shape": {"rows": 100, "columns": 5},
    "missing_values": {"has_missing": True},
    "has_non_normal": True,
    "categorical_columns": []
}

methods = rag.retrieve_method_cards(
    query="impute missing values",
    data_profile=data_profile,  # Filters by constraints
    k=3
)

for card, applicability_score in methods:
    passes, _ = card.matches_data_profile(data_profile)
    print(f"{card.method_name}: {'✓' if passes else '✗'} (score: {applicability_score:.2f})")
```

---

## Method Card Structure

Each method card contains:

```yaml
method_name: "LogisticRegression"
category: "model_classification"
problem_type: "binary_classification"

data_conditions:
  sample_size_min: 50
  sample_size_max: null
  normality_required: false
  handles_missing: false
  handles_categorical: false
  supports_multiclass: true

assumptions:
  - "Linear relationship between features and log-odds"
  - "Independence of observations"

when_to_use: "Good baseline for binary or multiclass classification..."
when_not_to_use: "Non-linear decision boundaries. Very high-dimensional data..."

alternatives: ["RandomForestClassifier", "GradientBoostingClassifier"]

code_example: |
  from sklearn.linear_model import LogisticRegression
  model = LogisticRegression(max_iter=1000)
  model.fit(X_train, y_train)

parameters:
  penalty: "Regularization type ('l1', 'l2', 'elasticnet')"
  C: "Inverse regularization strength"

source_url: "https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html"
source_license: "BSD-3-Clause"
library: "sklearn"
library_version: "1.8.0"
```

---

## Creating Your Own Method Cards

### Directory Structure

```
testing/method_cards/
├── classification_models.yaml     # LogisticRegression, RandomForest, etc.
├── regression_models.yaml         # LinearRegression, Ridge, Lasso, etc.
├── normality_tests.yaml          # Shapiro-Wilk, Anderson-Darling, etc.
├── correlation_tests.yaml        # Pearson, Spearman, Kendall
├── imputation.yaml               # SimpleImputer variants
├── scaling.yaml                  # StandardScaler, MinMaxScaler, etc.
└── encoding.yaml                 # LabelEncoder, OneHotEncoder, etc.
```

### Card Template

```yaml
- method_name: "YourMethodName"
  category: "model_classification|model_regression|stats_normality|preprocessing_imputation|..."
  problem_type: "binary_classification|regression|normality_test|missing_values|..."
  
  data_conditions:
    sample_size_min: 100              # null if no minimum
    sample_size_max: 10000            # null if unlimited
    sample_size_recommended: 1000
    normality_required: false
    handles_non_normal: true
    handles_missing: false
    requires_complete_data: true
    handles_categorical: false
    requires_numeric: true
    supports_binary_target: true
    supports_multiclass_target: false
    supports_continuous_target: false
    requires_independence: true
    handles_outliers: true
    requires_balanced_classes: false
  
  assumptions:
    - "First key assumption"
    - "Second key assumption"
  
  when_to_use: "Describe scenarios where this method excels..."
  
  when_not_to_use: "Describe when NOT to use this method..."
  
  alternatives: ["Alternative1", "Alternative2"]
  
  code_example: |
    # Minimal working example
    from library import Method
    model = Method(params)
    model.fit(X, y)
  
  parameters:
    param1: "Description of parameter"
    param2: "Description of parameter"
  
  source_url: "https://official-docs-url"
  source_license: "BSD-3-Clause|MIT|Apache-2.0|..."
  library: "sklearn|scipy|statsmodels|pandas"
  library_version: "1.0.0"
  supporting_excerpt: "Quote from official documentation with attribution"
  last_updated: "2025-12-21"
  confidence: 1.0
```

### Categories and Problem Types

**Available Categories**:
```python
MethodCategory.MODEL_CLASSIFICATION
MethodCategory.MODEL_REGRESSION
MethodCategory.PREPROCESSING_IMPUTATION
MethodCategory.PREPROCESSING_SCALING
MethodCategory.PREPROCESSING_ENCODING
MethodCategory.STATS_NORMALITY
MethodCategory.STATS_CORRELATION
MethodCategory.STATS_COMPARISON
```

**Available Problem Types**:
```python
ProblemType.BINARY_CLASSIFICATION
ProblemType.MULTICLASS_CLASSIFICATION
ProblemType.REGRESSION
ProblemType.NORMALITY_TEST
ProblemType.CORRELATION
ProblemType.GROUP_COMPARISON
ProblemType.MISSING_VALUES
ProblemType.FEATURE_SCALING
ProblemType.CATEGORICAL_ENCODING
```

To add new categories/types, edit `src/rag/method_card.py`.

---

## Retrieval Methods

### 1. Generic Method Retrieval

```python
methods = rag.retrieve_method_cards(
    query="your query",
    data_profile=optional_profile,
    k=5,
    filter_dict={"category": "model_classification"}
)
```

### 2. Category-Specific Retrieval

```python
# Preprocessing methods
methods = rag.retrieve_methods_for_preprocessing(
    query="handle missing values",
    data_profile=profile,
    k=3
)

# Statistical tests
methods = rag.retrieve_methods_for_statistics(
    query="test normality",
    data_profile=profile,
    k=3
)

# Model selection
methods = rag.retrieve_methods_for_modeling(
    query="binary classification",
    data_profile=profile,
    k=3
)
```

### 3. Constraint Matching

The system automatically filters methods based on your data profile:

```python
data_profile = {
    "shape": {"rows": 500, "columns": 10},
    "missing_values": {"has_missing": True},
    "has_non_normal": True,
    "categorical_columns": ["gender", "country"]
}

# Will exclude methods with:
# - sample_size_min > 500
# - sample_size_max < 500
# - requires_complete_data: true
# - normality_required: true (if has_non_normal)
```

---

## Using Custom Vector Stores

The method card system currently uses **LanceDB** by default, but can be adapted to other vector stores.

### Option 1: Use LanceDB (Recommended)

**Advantages**:
- ✅ Metadata filtering built-in
- ✅ Local storage (no external service)
- ✅ Fast and lightweight
- ✅ Supports constraint-based retrieval

**Setup**:
```python
# Already configured - just run load_method_cards.py
python testing/load_method_cards.py
```

### Option 2: Adapt to Your Vector Store

If you prefer a different vector store (FAISS, Weaviate, Pinecone, etc.), you'll need to:

#### Step 1: Create a Custom Loader

```python
# testing/load_method_cards_custom.py
from your_vector_store import YourVectorStore
from src.rag.method_card import load_all_method_cards
from langchain_core.documents import Document
import json

# Load method cards from YAML
cards = load_all_method_cards("testing/method_cards/")

# Convert to documents
documents = []
for card in cards:
    doc = Document(
        page_content=card.to_embedding_text(),
        metadata=card.to_metadata()
    )
    # Store full card as JSON
    doc.metadata["card_json"] = json.dumps(card.to_dict())
    documents.append(doc)

# Store in your vector store
vector_store = YourVectorStore(...)
vector_store.add_documents(documents)
```

#### Step 2: Update RAG System

```python
# src/rag/rag_system.py - modify retrieve_method_cards()

def retrieve_method_cards(self, query, data_profile=None, k=5):
    # Use your vector store instead of LanceDB
    from your_vector_store import YourVectorStore
    
    method_store = YourVectorStore(...)
    docs = method_store.similarity_search(query, k=k*3)
    
    # Parse method cards from results
    method_cards = []
    for doc in docs:
        metadata_json = doc.metadata.get("metadata_json")
        if metadata_json:
            metadata_dict = json.loads(metadata_json)
            card_json = metadata_dict.get("card_json")
            if card_json:
                card_dict = json.loads(card_json)
                card = MethodCard.from_dict(card_dict)
                method_cards.append(card)
    
    # Apply constraint filtering if data_profile provided
    if data_profile:
        scored_cards = []
        for card in method_cards:
            passes, score = card.matches_data_profile(data_profile)
            if passes or score > 0.3:
                scored_cards.append((card, score))
        scored_cards.sort(key=lambda x: x[1], reverse=True)
        return scored_cards[:k]
    
    return [(card, 1.0) for card in method_cards[:k]]
```

#### Step 3: Key Requirements

Your vector store must support:
1. **Embedding storage**: Store embeddings for semantic search
2. **Metadata storage**: Store `metadata_json` field containing full method card
3. **Similarity search**: Vector search with k results
4. **(Optional) Metadata filtering**: Filter by `category`, `topic`, `source` for better performance

---

## Testing

### Test Method Card Retrieval

```bash
python testing/test_method_card_retrieval.py
```

**Expected Output**:
```
🧪 TEST 1: Basic Method Card Retrieval
📋 Query: 'how to handle missing values'
   ✅ Found 3 methods:
      • SimpleImputer (mean) (preprocessing_imputation) - confidence: 1.00
      • SimpleImputer (median) (preprocessing_imputation) - confidence: 1.00
      • SimpleImputer (mode) (preprocessing_imputation) - confidence: 1.00

🧪 TEST 2: Constraint-Based Retrieval
📊 Data Profile: 100 rows, missing values, non-normal
📋 Query: 'impute missing values'
   ✅ Found 3 applicable methods:
      • SimpleImputer (mean) - applicability: 1.00 ✓
      • SimpleImputer (median) - applicability: 1.00 ✓
      • SimpleImputer (mode) - applicability: 1.00 ✓
```

---

## Expanding the Knowledge Base

### Current Coverage (16 Methods)

**Classification Models (4)**:
- LogisticRegression, RandomForestClassifier, GradientBoostingClassifier, SVC

**Normality Tests (3)**:
- Shapiro-Wilk, Anderson-Darling, Kolmogorov-Smirnov

**Correlation Tests (3)**:
- Pearson, Spearman, Kendall Tau

**Imputation (3)**:
- SimpleImputer (mean, median, mode)

**Scaling (3)**:
- StandardScaler, MinMaxScaler, RobustScaler

### Recommended Additions (Target: 30-60 Methods)

**Regression Models**:
- LinearRegression, Ridge, Lasso, ElasticNet, RandomForestRegressor

**More Classification**:
- KNeighborsClassifier, DecisionTreeClassifier, XGBClassifier, LGBMClassifier

**Encoding**:
- LabelEncoder, OneHotEncoder, OrdinalEncoder, TargetEncoder

**Feature Selection**:
- SelectKBest, RFE, VarianceThreshold

**Dimensionality Reduction**:
- PCA, t-SNE, UMAP

**Statistical Tests**:
- t-test, Mann-Whitney U, Chi-square, ANOVA, Kruskal-Wallis

**Outlier Detection**:
- IsolationForest, LocalOutlierFactor, DBSCAN

### Adding New Methods

1. Create YAML card in `testing/method_cards/`
2. Run loader: `python testing/load_method_cards.py`
3. Test: `python testing/test_method_card_retrieval.py`

---

## Troubleshooting

### Issue: "Table 'method_cards' not found"

**Solution**:
```bash
python testing/load_method_cards.py
```

### Issue: "No results found"

**Check**:
1. Method cards loaded: `ls -la lancedb/method_cards.lance`
2. Query matches method descriptions: Try broader queries
3. Data profile too restrictive: Relax constraints

### Issue: "JSON parsing error"

**Solution**: Delete and reload (already fixed in latest version)
```bash
rm -rf lancedb/method_cards.lance
python testing/load_method_cards.py
```

---

## Best Practices

1. **Curate Quality Over Quantity**: 30-60 well-documented cards >> 500 raw chunks
2. **Keep Cards Updated**: Update `library_version` and `last_updated` regularly
3. **Provide Real Constraints**: Use actual sample size limits from documentation
4. **Include Alternatives**: Help users discover better methods
5. **Attribute Sources**: Always include `source_url` and `source_license`
6. **Test Retrieval**: Run `test_method_card_retrieval.py` after adding cards

---

## License & Attribution

All method cards must include:
- `source_url`: Link to official documentation
- `source_license`: License of the source library
- `supporting_excerpt`: Attributed quote from documentation

This ensures legal compliance and gives credit to original authors.

**Example Attribution**:
```yaml
source_url: "https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html"
source_license: "BSD-3-Clause"
supporting_excerpt: "A random forest is a meta estimator that fits a number of decision tree classifiers on various sub-samples of the dataset and uses averaging to improve the predictive accuracy and control over-fitting. - scikit-learn documentation"
```

---

## FAQ

**Q: Can I use method cards without LanceDB?**  
A: Yes, but you'll need to implement a custom loader for your vector store (see "Using Custom Vector Stores" section).

**Q: How do I add methods from custom libraries?**  
A: Create a new YAML file with your method cards, set `library: "your_library"`, and load normally.

**Q: Can method cards replace all RAG documentation?**  
A: Method cards are for decision-making ("what method to use"). For implementation details, the `code_example` and `source_url` guide users to full documentation.

**Q: How often should I update method cards?**  
A: Update when library versions change significantly or when constraints/best practices evolve (every 6-12 months).

**Q: Can I auto-generate method cards from documentation?**  
A: Not recommended. Method cards require expert curation to extract decision criteria, constraints, and assumptions that aren't explicitly stated in docs.

---

## Support

For issues or questions:
1. Check this guide
2. Run tests: `python testing/test_method_card_retrieval.py`
3. Review example cards in `testing/method_cards/`
4. Open an issue on GitHub

**Happy curating! 🎉**
