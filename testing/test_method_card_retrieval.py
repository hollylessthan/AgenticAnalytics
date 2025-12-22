"""Test method card retrieval from LanceDB."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.rag_system import RAGSystem
from src.config import config

def test_basic_retrieval():
    """Test basic method card retrieval without data profile."""
    print("="*60)
    print("🧪 TEST 1: Basic Method Card Retrieval")
    print("="*60)
    
    rag = RAGSystem()
    
    # Test queries
    test_cases = [
        ("how to handle missing values", "preprocessing"),
        ("test if data is normally distributed", "stats"),
        ("binary classification model", "model"),
        ("correlation between variables", "stats"),
        ("scale features for machine learning", "preprocessing"),
    ]
    
    for query, expected_topic in test_cases:
        print(f"\n📋 Query: '{query}'")
        print(f"   Expected: {expected_topic}")
        
        try:
            results = rag.retrieve_method_cards(query, k=3)
            
            if results:
                print(f"   ✅ Found {len(results)} methods:")
                for card, score in results:
                    print(f"      • {card.method_name} ({card.category.value}) - confidence: {score:.2f}")
                    print(f"        {card.when_to_use[:80]}...")
            else:
                print(f"   ❌ No results found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")


def test_constraint_based_retrieval():
    """Test constraint-based retrieval with data profile."""
    print("\n" + "="*60)
    print("🧪 TEST 2: Constraint-Based Retrieval")
    print("="*60)
    
    rag = RAGSystem()
    
    # Simulated data profile (small dataset with missing values)
    small_dataset_profile = {
        "shape": {"rows": 100, "columns": 5},
        "missing_values": {
            "has_missing": True,
            "columns_with_missing": ["age", "income"]
        },
        "has_non_normal": True,
        "categorical_columns": []
    }
    
    print("\n📊 Data Profile:")
    print(f"   • Rows: 100")
    print(f"   • Missing values: Yes")
    print(f"   • Non-normal distribution: Yes")
    
    # Test 1: Imputation methods should match constraints
    print(f"\n📋 Query: 'impute missing values'")
    results = rag.retrieve_method_cards(
        "impute missing values",
        data_profile=small_dataset_profile,
        k=3
    )
    
    if results:
        print(f"   ✅ Found {len(results)} applicable methods:")
        for card, score in results:
            print(f"      • {card.method_name} - applicability: {score:.2f}")
            passes, _ = card.matches_data_profile(small_dataset_profile)
            print(f"        Passes constraints: {passes}")
    
    # Test 2: Large dataset (should exclude methods with max sample size)
    large_dataset_profile = {
        "shape": {"rows": 50000, "columns": 10},
        "missing_values": {"has_missing": False},
        "has_non_normal": False,
        "categorical_columns": []
    }
    
    print(f"\n📋 Query: 'classification model' (50k samples)")
    results = rag.retrieve_method_cards(
        "classification model",
        data_profile=large_dataset_profile,
        k=3
    )
    
    if results:
        print(f"   ✅ Found {len(results)} applicable methods:")
        for card, score in results:
            max_samples = card.data_conditions.sample_size_max
            print(f"      • {card.method_name} - max samples: {max_samples or 'unlimited'}")


def test_category_filtering():
    """Test retrieval with category filters."""
    print("\n" + "="*60)
    print("🧪 TEST 3: Category-Specific Retrieval")
    print("="*60)
    
    rag = RAGSystem()
    
    # Test preprocessing methods
    print(f"\n📋 Preprocessing methods:")
    results = rag.retrieve_methods_for_preprocessing("handle missing data", k=3)
    if results:
        for card, score in results:
            print(f"   • {card.method_name} ({card.category.value})")
    
    # Test statistical tests
    print(f"\n📋 Statistical tests:")
    results = rag.retrieve_methods_for_statistics("test normality", k=3)
    if results:
        for card, score in results:
            print(f"   • {card.method_name} ({card.category.value})")
    
    # Test models
    print(f"\n📋 Classification models:")
    results = rag.retrieve_methods_for_modeling("binary classification", k=3)
    if results:
        for card, score in results:
            print(f"   • {card.method_name} ({card.category.value})")


def main():
    """Run all tests."""
    print("\n🚀 METHOD CARD RETRIEVAL TESTS")
    print("="*60)
    
    test_basic_retrieval()
    test_constraint_based_retrieval()
    test_category_filtering()
    test_regression_methods()
    test_anova_methods()
    test_evaluation_metrics()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETE")
    print("="*60)


def test_regression_methods():
    """Test retrieval of regression methods (OLS, Ridge, Lasso, GLS)."""
    print("\n" + "="*60)
    print("🧪 TEST 4: Regression Methods Retrieval")
    print("="*60)
    
    rag = RAGSystem()
    
    # Test 1: OLS for linear regression
    print(f"\n📋 Query: 'linear regression with interpretable coefficients'")
    results = rag.retrieve_method_cards(
        "linear regression with interpretable coefficients and statistical significance",
        k=3
    )
    if results:
        print(f"   ✅ Found {len(results)} methods:")
        for card, score in results:
            print(f"      • {card.method_name} - confidence: {score:.2f}")
            if "OLS" in card.method_name or "Linear Regression" in card.method_name:
                print(f"        ✓ Correct: Found OLS/Linear Regression")
    
    # Test 2: Ridge for multicollinearity
    print(f"\n📋 Query: 'regression with correlated features multicollinearity'")
    results = rag.retrieve_method_cards(
        "regression when predictors are highly correlated multicollinearity",
        k=3
    )
    if results:
        print(f"   ✅ Found {len(results)} methods:")
        for card, score in results:
            print(f"      • {card.method_name} - confidence: {score:.2f}")
            if "Ridge" in card.method_name or "Elastic" in card.method_name:
                print(f"        ✓ Correct: Found Ridge/Elastic Net")
    
    # Test 3: Lasso for feature selection
    print(f"\n📋 Query: 'regression with automatic feature selection'")
    results = rag.retrieve_method_cards(
        "regression with automatic feature selection sparse model",
        k=3
    )
    if results:
        print(f"   ✅ Found {len(results)} methods:")
        for card, score in results:
            print(f"      • {card.method_name} - confidence: {score:.2f}")
            if "Lasso" in card.method_name or "Elastic" in card.method_name:
                print(f"        ✓ Correct: Found Lasso/Elastic Net")
    
    # Test 4: GLS for heteroscedasticity
    print(f"\n📋 Query: 'regression with heteroscedasticity or autocorrelation'")
    results = rag.retrieve_method_cards(
        "regression when errors have non-constant variance or autocorrelation",
        k=3
    )
    if results:
        print(f"   ✅ Found {len(results)} methods:")
        for card, score in results:
            print(f"      • {card.method_name} - confidence: {score:.2f}")
            if "GLS" in card.method_name:
                print(f"        ✓ Correct: Found GLS")


def test_anova_methods():
    """Test retrieval of ANOVA and group comparison tests."""
    print("\n" + "="*60)
    print("🧪 TEST 5: ANOVA and Group Comparison Tests")
    print("="*60)
    
    rag = RAGSystem()
    
    # Test 1: ANOVA for multiple groups
    print(f"\n📋 Query: 'compare means across multiple groups'")
    results = rag.retrieve_method_cards(
        "compare means of three or more groups ANOVA",
        k=3
    )
    if results:
        print(f"   ✅ Found {len(results)} methods:")
        for card, score in results:
            print(f"      • {card.method_name} - confidence: {score:.2f}")
            if "ANOVA" in card.method_name:
                print(f"        ✓ Correct: Found ANOVA")
    
    # Test 2: t-test for two groups
    print(f"\n📋 Query: 'compare two groups independent samples'")
    results = rag.retrieve_method_cards(
        "compare means of two independent groups t-test",
        k=3
    )
    if results:
        print(f"   ✅ Found {len(results)} methods:")
        for card, score in results:
            print(f"      • {card.method_name} - confidence: {score:.2f}")
            if "t-test" in card.method_name and "Independent" in card.method_name:
                print(f"        ✓ Correct: Found Independent t-test")
    
    # Test 3: Paired t-test
    print(f"\n📋 Query: 'before after comparison same subjects'")
    results = rag.retrieve_method_cards(
        "compare before and after measurements on same subjects paired",
        k=3
    )
    if results:
        print(f"   ✅ Found {len(results)} methods:")
        for card, score in results:
            print(f"      • {card.method_name} - confidence: {score:.2f}")
            if "Paired" in card.method_name:
                print(f"        ✓ Correct: Found Paired t-test")
    
    # Test 4: Non-parametric tests
    print(f"\n📋 Query: 'compare groups with non-normal data'")
    results = rag.retrieve_method_cards(
        "compare groups when data is not normally distributed non-parametric",
        k=3
    )
    if results:
        print(f"   ✅ Found {len(results)} methods:")
        for card, score in results:
            print(f"      • {card.method_name} - confidence: {score:.2f}")
            if "Kruskal" in card.method_name or "Mann-Whitney" in card.method_name:
                print(f"        ✓ Correct: Found non-parametric test")
    
    # Test 5: Chi-square for categorical
    print(f"\n📋 Query: 'test association between categorical variables'")
    results = rag.retrieve_method_cards(
        "test independence between two categorical variables chi-square",
        k=3
    )
    if results:
        print(f"   ✅ Found {len(results)} methods:")
        for card, score in results:
            print(f"      • {card.method_name} - confidence: {score:.2f}")
            if "Chi-Square" in card.method_name:
                print(f"        ✓ Correct: Found Chi-Square test")


def test_evaluation_metrics():
    """Test retrieval of evaluation metrics and interpretation guides."""
    print("\n" + "="*60)
    print("🧪 TEST 6: Evaluation Metrics and Interpretation")
    print("="*60)
    
    rag = RAGSystem()
    
    # Test 1: Regression metrics
    print(f"\n📋 Query: 'evaluate regression model performance'")
    results = rag.retrieve_method_cards(
        "metrics to evaluate regression model accuracy MSE RMSE R-squared",
        k=5
    )
    if results:
        print(f"   ✅ Found {len(results)} regression metrics:")
        for card, score in results:
            print(f"      • {card.method_name} - confidence: {score:.2f}")
            if any(metric in card.method_name for metric in ["MSE", "RMSE", "MAE", "R²"]):
                print(f"        ✓ Correct: Found regression metric")
    
    # Test 2: Classification metrics
    print(f"\n📋 Query: 'evaluate binary classifier performance'")
    results = rag.retrieve_method_cards(
        "metrics for binary classification precision recall AUC ROC",
        k=5
    )
    if results:
        print(f"   ✅ Found {len(results)} classification metrics:")
        for card, score in results:
            print(f"      • {card.method_name} - confidence: {score:.2f}")
            if any(metric in card.method_name for metric in ["AUC", "Precision", "Recall", "F1"]):
                print(f"        ✓ Correct: Found classification metric")
    
    # Test 3: P-value interpretation
    print(f"\n📋 Query: 'how to interpret p-value statistical significance'")
    results = rag.retrieve_method_cards(
        "interpret p-value statistical significance hypothesis testing",
        k=3
    )
    if results:
        print(f"   ✅ Found {len(results)} interpretation guides:")
        for card, score in results:
            print(f"      • {card.method_name} - confidence: {score:.2f}")
            if "P-Value" in card.method_name:
                print(f"        ✓ Correct: Found P-Value interpretation guide")
    
    # Test 4: Imbalanced dataset metrics
    print(f"\n📋 Query: 'metrics for imbalanced classification dataset'")
    results = rag.retrieve_method_cards(
        "evaluation metrics for imbalanced dataset F1 score precision recall",
        k=3
    )
    if results:
        print(f"   ✅ Found {len(results)} methods:")
        for card, score in results:
            print(f"      • {card.method_name} - confidence: {score:.2f}")
            if any(metric in card.method_name for metric in ["F1", "Precision", "Recall", "AUC"]):
                print(f"        ✓ Correct: Found imbalanced dataset metric")


if __name__ == "__main__":
    main()
