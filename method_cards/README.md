# Method Cards - Statistical and Machine Learning Method Knowledge Base

This directory contains curated method cards that provide structured knowledge about statistical tests, machine learning algorithms, preprocessing techniques, and evaluation metrics. Each card includes detailed information about when to use a method, its assumptions, interpretation guidelines, and data constraints.

## 📋 Overview

Method cards are YAML files that store comprehensive information about analytical methods. They enable intelligent method recommendation based on:
- **Data characteristics** (sample size, missing values, normality, etc.)
- **Problem type** (regression, classification, comparison, preprocessing)
- **Specific constraints** (multicollinearity, heteroscedasticity, paired data, etc.)

## 📚 Current Method Cards

### Classification Models (`classification_models.yaml`)
- Logistic Regression
- Random Forest Classifier
- Gradient Boosting Classifier
- Support Vector Classifier (SVC)

### Regression Models (`regression_models.yaml`)
- Linear Regression (OLS)
- Ridge Regression (L2)
- Lasso Regression (L1)
- Elastic Net Regression
- Generalized Least Squares (GLS)
- Logistic Regression (for classification)

### Group Comparison & Hypothesis Tests (`group_comparison_tests.yaml`)
- One-Way ANOVA
- Two-Sample t-test (Independent)
- Paired t-test
- Kruskal-Wallis H Test
- Mann-Whitney U Test
- Chi-Square Test of Independence
- One-Sample z-test
- Two-Sample z-test
- Binomial Test

### Normality Tests (`normality_tests.yaml`)
- Shapiro-Wilk Test
- Kolmogorov-Smirnov Test
- Anderson-Darling Test

### Correlation Tests (`correlation_tests.yaml`)
- Pearson Correlation
- Spearman Rank Correlation
- Kendall's Tau

### Imputation Methods (`imputation.yaml`)
- Simple Imputer (Mean)
- Simple Imputer (Median)
- Simple Imputer (Most Frequent)

### Scaling Methods (`scaling.yaml`)
- StandardScaler (Z-score normalization)
- MinMaxScaler
- RobustScaler

### Evaluation Metrics (`evaluation_metrics.yaml`)
- Mean Squared Error (MSE)
- Root Mean Squared Error (RMSE)
- Mean Absolute Error (MAE)
- R² (Coefficient of Determination)
- Adjusted R²
- AUC-ROC
- Precision
- Recall
- F1-Score
- P-Value Interpretation

## 📖 Sources and References

All method cards are derived from widely-accepted statistical and machine learning literature and documentation:

### Primary Sources:
1. **Scikit-learn Documentation** (BSD 3-Clause License)
   - https://scikit-learn.org/stable/documentation.html
   - Machine learning algorithms, preprocessing, evaluation metrics

2. **SciPy Documentation** (BSD 3-Clause License)
   - https://docs.scipy.org/doc/scipy/reference/stats.html
   - Statistical tests and distributions

3. **Statsmodels Documentation** (BSD 3-Clause License)
   - https://www.statsmodels.org/stable/index.html
   - OLS, GLS, ANOVA, statistical modeling

4. **Standard Statistical Textbooks** (Educational Fair Use):
   - "Applied Linear Statistical Models" by Kutner, Nachtsheim, Neter, Li
   - "An Introduction to Statistical Learning" by James, Witten, Hastie, Tibshirani
   - "The Elements of Statistical Learning" by Hastie, Tibshirani, Friedman
   - "Practical Statistics for Data Scientists" by Bruce, Bruce, Gedeck

### Knowledge Compilation:
- Method cards synthesize information from multiple authoritative sources
- No copyrighted text is directly copied
- All interpretations and explanations are original summaries
- Mathematical formulas are standard statistical/ML notation (not copyrightable)

## ⚖️ Licensing and Legal

### Method Cards License:
These method cards are original works created for the AgenticAnalytics project and are released under the **Apache License 2.0** (same as the main project).

### Factual Information:
- Statistical methods and algorithms are mathematical facts (not copyrightable)
- Parameter names and function signatures from scikit-learn/scipy/statsmodels are factual references
- Mathematical formulas are standard notation in the public domain

### Fair Use Statement:
Where educational materials are referenced:
- Used for educational and research purposes
- Transformative use (synthesis into structured knowledge base)
- No substantial copying of original expression
- Does not substitute for original sources

## 🔧 Usage

### Loading Method Cards

```python
from pathlib import Path
from testing.load_method_cards import load_all_method_cards

# Load all method cards
cards_dir = Path("method_cards")
cards = load_all_method_cards(cards_dir)

# Print summary
for card in cards:
    print(f"{card.method_name} ({card.category.value})")
```

### Querying Method Cards

```python
from src.rag.rag_system import RAGSystem

rag = RAGSystem()

# Find methods for a specific task
results = rag.retrieve_method_cards(
    "handle missing values in dataset",
    k=3
)

for card, score in results:
    print(f"{card.method_name}: {card.when_to_use}")
```

### Constraint-Based Retrieval

```python
# Define data profile
data_profile = {
    "shape": {"rows": 100, "columns": 5},
    "missing_values": {"has_missing": True},
    "has_non_normal": True,
}

# Get applicable methods
results = rag.retrieve_method_cards(
    "impute missing values",
    data_profile=data_profile,
    k=3
)
```

## 🤝 Contributing

We welcome contributions of new method cards! When adding methods:

1. **Use the existing YAML schema** (see any existing card for template)
2. **Provide comprehensive information**:
   - Clear `when_to_use` guidance
   - Complete list of assumptions
   - Detailed interpretation guide
   - Appropriate data conditions
3. **Cite your sources** in this README
4. **Ensure original expression** - synthesize information, don't copy text
5. **Test the card** using `testing/test_method_card_retrieval.py`

### Adding a New Method Card

1. Choose appropriate YAML file or create new category
2. Follow the schema (see example below)
3. Add entry to the "Current Method Cards" section above
4. Document sources in "Sources and References" section
5. Run loader and tests to validate

### Example Card Structure

```yaml
- method_name: "Your Method Name"
  category: "model|stats|preprocessing|evaluation"
  problem_type: "regression|classification|comparison|preprocessing|evaluation"
  scikit_learn_name: "ClassName or null"
  statsmodels_name: "function_name or null"
  scipy_name: "function_name or null"
  python_package: "sklearn|scipy|statsmodels"
  when_to_use: "Clear guidance on when this method is appropriate..."
  assumptions:
    - "List all statistical/mathematical assumptions"
  typical_use_cases:
    - "Real-world example 1"
    - "Real-world example 2"
  interpretation_guide: "Detailed explanation of how to interpret results..."
  evaluation_metrics:
    - "Metric 1"
    - "Metric 2"
  data_conditions:
    sample_size_min: 30
    # ... other constraints (see existing cards)
```

## 📊 Method Card Schema

Each method card contains:
- **Identification**: method_name, category, problem_type
- **Implementation**: scikit_learn_name, statsmodels_name, scipy_name, python_package
- **Usage Guidance**: when_to_use, assumptions, typical_use_cases
- **Interpretation**: interpretation_guide, evaluation_metrics
- **Constraints**: data_conditions (15+ fields for intelligent matching)

## 🔍 Quality Assurance

All method cards undergo:
1. **Technical review** - Verify accuracy of assumptions and interpretations
2. **Schema validation** - Ensure proper YAML structure
3. **Retrieval testing** - Validate semantic search finds appropriate methods
4. **Constraint testing** - Verify data_conditions filter correctly

---

**Note**: This knowledge base is continually expanding. Current coverage: ~40 methods across 8 categories. Target: 60-100 methods covering the full spectrum of data science workflows.
