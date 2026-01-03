"""Method Card schema for structured ML/stats knowledge base.

Instead of chunking raw documentation, we curate structured "method cards"
containing decision criteria, constraints, and usage guidance.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from enum import Enum


class MethodCategory(Enum):
    """Category of method."""
    MODEL_CLASSIFICATION = "model_classification"
    MODEL_REGRESSION = "model_regression"
    MODEL = "model"  # General model category
    PREPROCESSING_IMPUTATION = "preprocessing_imputation"
    PREPROCESSING_SCALING = "preprocessing_scaling"
    PREPROCESSING_ENCODING = "preprocessing_encoding"
    PREPROCESSING_TRANSFORMATION = "preprocessing_transformation"
    PREPROCESSING_OUTLIER_HANDLING = "preprocessing_outlier_handling"
    STATS_NORMALITY = "stats_normality"
    STATS_CORRELATION = "stats_correlation"
    STATS_COMPARISON = "stats_comparison"
    STATS = "stats"  # General stats category
    EVALUATION = "evaluation"  # Evaluation metrics


class ProblemType(Enum):
    """Type of problem the method addresses."""
    BINARY_CLASSIFICATION = "binary_classification"
    MULTICLASS_CLASSIFICATION = "multiclass_classification"
    CLASSIFICATION = "classification"  # General classification
    REGRESSION = "regression"
    NORMALITY_TEST = "normality_test"
    CORRELATION = "correlation"
    GROUP_COMPARISON = "group_comparison"
    COMPARISON = "comparison"  # General comparison/hypothesis test
    MISSING_VALUES = "missing_values"
    FEATURE_SCALING = "feature_scaling"
    CATEGORICAL_ENCODING = "categorical_encoding"
    PREPROCESSING = "preprocessing"  # General preprocessing
    EVALUATION = "evaluation"  # Performance evaluation
    STATISTICAL_TEST = "statistical_test"  # General statistical test
    FEATURE_ENGINEERING = "feature_engineering"


@dataclass
class DataConditions:
    """Data requirements and constraints for a method."""
    
    # Sample size
    sample_size_min: Optional[int] = None
    sample_size_max: Optional[int] = None
    sample_size_recommended: Optional[int] = None  # Backward compatibility
    sample_size_recommended: Optional[int] = None  # For backward compatibility
    
    # Distribution requirements
    requires_normality: bool = False
    normality_required: Optional[bool] = None  # Backward compatibility alias
    handles_non_normal: Optional[bool] = None  # Backward compatibility alias
    handles_missing_values: bool = False
    handles_missing: Optional[bool] = None  # Backward compatibility alias
    requires_complete_data: Optional[bool] = None  # Backward compatibility alias
    handles_categorical: bool = False
    requires_numeric: Optional[bool] = None  # Backward compatibility alias
    
    # Statistical assumptions
    requires_independence: bool = False
    sensitive_to_outliers: bool = False
    requires_balanced: bool = False
    requires_balanced_classes: Optional[bool] = None  # Backward compatibility alias
    handles_outliers: Optional[bool] = None  # Backward compatibility alias
    requires_homoscedasticity: Optional[bool] = None
    requires_linearity: Optional[bool] = None
    handles_multicollinearity: Optional[bool] = None
    
    # Target variable (backward compatibility)
    supports_binary_target: Optional[bool] = None
    supports_multiclass_target: Optional[bool] = None
    supports_continuous_target: Optional[bool] = None
    
    # Categories
    min_categories: Optional[int] = None
    max_categories: Optional[int] = None
    
    # Paired data
    requires_paired: bool = False
    
    # Features
    min_features: Optional[int] = None
    max_features: Optional[int] = None
    
    def __post_init__(self):
        """Handle backward compatibility aliases."""
        # Map old field names to new ones
        if self.normality_required is not None:
            self.requires_normality = self.normality_required
        if self.handles_missing is not None:
            self.handles_missing_values = self.handles_missing
        if self.requires_complete_data is not None:
            self.handles_missing_values = not self.requires_complete_data
        if self.requires_balanced_classes is not None:
            self.requires_balanced = self.requires_balanced_classes
        if self.handles_outliers is not None:
            self.sensitive_to_outliers = not self.handles_outliers
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def matches(self, data_profile: Dict[str, Any]) -> tuple[bool, float]:
        """Check if data profile matches conditions.
        
        Args:
            data_profile: Data profile from ProfilingAgent
            
        Returns:
            Tuple of (passes_hard_constraints, match_score)
        """
        hard_constraints_pass = True
        match_score = 1.0
        
        # Hard constraints - sample size
        if self.sample_size_min:
            n_rows = data_profile.get("shape", {}).get("rows", 0)
            if n_rows < self.sample_size_min:
                hard_constraints_pass = False
                match_score *= 0.5
        
        if self.sample_size_max:
            n_rows = data_profile.get("shape", {}).get("rows", float('inf'))
            if n_rows > self.sample_size_max:
                hard_constraints_pass = False
                match_score *= 0.5
        
        # Hard constraints - missing values
        if not self.handles_missing_values:
            has_missing = data_profile.get("missing_values", {}).get("has_missing", False)
            if has_missing:
                hard_constraints_pass = False
                match_score *= 0.3
        
        # Hard constraints - categorical data
        if not self.handles_categorical:
            has_categorical = len(data_profile.get("categorical_columns", [])) > 0
            if has_categorical:
                hard_constraints_pass = False
                match_score *= 0.4
        
        # Soft constraints - normality
        if self.requires_normality:
            has_non_normal = data_profile.get("has_non_normal", False)
            if has_non_normal:
                match_score *= 0.7
        
        return hard_constraints_pass, match_score


@dataclass
class MethodCard:
    """Structured knowledge card for an ML/stats method.
    
    This replaces raw documentation chunks with curated decision units.
    """
    
    # Identity
    method_name: str
    category: MethodCategory
    problem_type: ProblemType
    
    # Implementation details
    scikit_learn_name: Optional[str] = None
    statsmodels_name: Optional[str] = None
    scipy_name: Optional[str] = None
    python_package: str = "sklearn"
    
    # Data requirements
    data_conditions: DataConditions = field(default_factory=lambda: DataConditions())
    
    # Decision guidance
    when_to_use: str = ""
    assumptions: List[str] = field(default_factory=list)
    typical_use_cases: List[str] = field(default_factory=list)
    interpretation_guide: str = ""
    evaluation_metrics: List[str] = field(default_factory=list)
    
    # Legacy fields (for backward compatibility)
    when_not_to_use: str = ""
    alternatives: List[str] = field(default_factory=list)
    code_example: str = ""
    parameters: Dict[str, str] = field(default_factory=dict)
    
    # Attribution
    source_url: str = ""
    source_license: str = ""
    library: str = ""
    library_version: str = ""
    supporting_excerpt: str = ""
    
    # Metadata
    last_updated: str = ""
    confidence: float = 1.0
    
    def to_embedding_text(self) -> str:
        """Convert card to text for embedding.
        
        This creates a rich semantic representation for vector search.
        """
        parts = [
            f"Method: {self.method_name}",
            f"Category: {self.category.value}",
            f"Problem: {self.problem_type.value}",
            f"When to use: {self.when_to_use}",
        ]
        
        if self.assumptions:
            parts.append(f"Assumptions: {', '.join(self.assumptions)}")
        
        if self.typical_use_cases:
            parts.append(f"Use cases: {', '.join(self.typical_use_cases)}")
        
        if self.interpretation_guide:
            # Add first 200 chars of interpretation guide
            parts.append(f"Interpretation: {self.interpretation_guide[:200]}")
        
        if self.when_not_to_use:
            parts.append(f"When NOT to use: {self.when_not_to_use}")
        
        if self.alternatives:
            parts.append(f"Alternatives: {', '.join(self.alternatives)}")
        
        # Add key data conditions
        if self.data_conditions.sample_size_min:
            parts.append(f"Minimum samples: {self.data_conditions.sample_size_min}")
        
        if self.data_conditions.requires_normality:
            parts.append("Requires normally distributed data")
        
        if self.data_conditions.handles_missing_values:
            parts.append("Handles missing values")
        
        return " | ".join(parts)
    
    def to_metadata(self) -> Dict[str, Any]:
        """Convert to metadata dict for vector store."""
        return {
            "method_name": self.method_name,
            "category": self.category.value,
            "problem_type": self.problem_type.value,
            "source": self.python_package or self.library,
            "topic": self.category.value.split("_")[0] if "_" in self.category.value else self.category.value,
            "doc_type": "method_card",
            "source_url": self.source_url,
            "source_license": self.source_license,
            # Data condition flags for filtering
            "sample_size_min": self.data_conditions.sample_size_min or 0,
            "sample_size_max": self.data_conditions.sample_size_max or 999999,
            "requires_normality": self.data_conditions.requires_normality,
            "handles_missing_values": self.data_conditions.handles_missing_values,
            "handles_categorical": self.data_conditions.handles_categorical,
        }
    
    def matches_data_profile(self, data_profile: Dict[str, Any]) -> tuple[bool, float]:
        """Check if this method is applicable to given data.
        
        Args:
            data_profile: Data profile from ProfilingAgent
            
        Returns:
            Tuple of (passes_constraints, applicability_score)
        """
        return self.data_conditions.matches(data_profile)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "method_name": self.method_name,
            "category": self.category.value,
            "problem_type": self.problem_type.value,
            "data_conditions": self.data_conditions.to_dict(),
            "assumptions": self.assumptions,
            "when_to_use": self.when_to_use,
            "when_not_to_use": self.when_not_to_use,
            "alternatives": self.alternatives,
            "code_example": self.code_example,
            "parameters": self.parameters,
            "source_url": self.source_url,
            "source_license": self.source_license,
            "library": self.library,
            "library_version": self.library_version,
            "supporting_excerpt": self.supporting_excerpt,
            "last_updated": self.last_updated,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MethodCard":
        """Create MethodCard from dictionary."""
        # Parse enums
        category = MethodCategory(data["category"])
        problem_type = ProblemType(data["problem_type"])
        
        # Parse data conditions
        data_conditions = DataConditions(**data["data_conditions"])
        
        return cls(
            method_name=data["method_name"],
            category=category,
            problem_type=problem_type,
            data_conditions=data_conditions,
            assumptions=data.get("assumptions", []),
            when_to_use=data.get("when_to_use", ""),
            when_not_to_use=data.get("when_not_to_use", ""),
            alternatives=data.get("alternatives", []),
            code_example=data.get("code_example", ""),
            parameters=data.get("parameters", {}),
            source_url=data.get("source_url", ""),
            source_license=data.get("source_license", ""),
            library=data.get("library", ""),
            library_version=data.get("library_version", ""),
            supporting_excerpt=data.get("supporting_excerpt", ""),
            last_updated=data.get("last_updated", ""),
            confidence=data.get("confidence", 1.0)
        )


def create_example_cards() -> List[MethodCard]:
    """Create example method cards for testing."""
    cards = [
        # Classification: Logistic Regression
        MethodCard(
            method_name="LogisticRegression",
            category=MethodCategory.MODEL_CLASSIFICATION,
            problem_type=ProblemType.BINARY_CLASSIFICATION,
            data_conditions=DataConditions(
                sample_size_min=50,
                sample_size_recommended=500,
                normality_required=False,
                handles_missing=False,
                requires_complete_data=True,
                handles_categorical=False,
                requires_numeric=True,
                supports_binary_target=True,
                supports_multiclass_target=True,
                supports_continuous_target=False,
            ),
            assumptions=[
                "Linear relationship between features and log-odds",
                "Independence of observations",
                "No multicollinearity among features"
            ],
            when_to_use="Good baseline for binary or multiclass classification. Fast training, interpretable coefficients. Works well with 100s-1000s samples.",
            when_not_to_use="Non-linear decision boundaries, very high-dimensional data (>10k features), highly imbalanced classes without adjustment.",
            alternatives=["RandomForestClassifier", "GradientBoostingClassifier", "SVC"],
            code_example="from sklearn.linear_model import LogisticRegression\nmodel = LogisticRegression(max_iter=1000)\nmodel.fit(X_train, y_train)",
            source_url="https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html",
            source_license="BSD-3-Clause",
            library="sklearn",
            library_version="1.8.0",
            supporting_excerpt="Logistic regression is a linear model for classification. It estimates probabilities using the logistic function.",
            last_updated="2025-12-21",
            confidence=1.0
        ),
        
        # Statistical test: Shapiro-Wilk
        MethodCard(
            method_name="Shapiro-Wilk",
            category=MethodCategory.STATS_NORMALITY,
            problem_type=ProblemType.NORMALITY_TEST,
            data_conditions=DataConditions(
                sample_size_min=3,
                sample_size_max=5000,
                sample_size_recommended=2000,
                normality_required=False,  # Testing FOR normality
                handles_missing=False,
                requires_complete_data=True,
            ),
            assumptions=[
                "Data is univariate (single variable)",
                "Samples are independent"
            ],
            when_to_use="Test if data follows normal distribution. Most powerful test for small-medium samples (n < 2000). Use before choosing parametric vs non-parametric tests.",
            when_not_to_use="Very large samples (n > 5000) - use Anderson-Darling instead. Multivariate data - use Mardia's test.",
            alternatives=["Anderson-Darling", "Kolmogorov-Smirnov", "Jarque-Bera"],
            code_example="from scipy.stats import shapiro\nstat, p_value = shapiro(data)\nif p_value > 0.05: print('Data looks normal')",
            source_url="https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.shapiro.html",
            source_license="BSD-3-Clause",
            library="scipy",
            library_version="1.11.0",
            supporting_excerpt="The Shapiro-Wilk test tests the null hypothesis that the data was drawn from a normal distribution.",
            last_updated="2025-12-21",
            confidence=1.0
        ),
    ]
    
    return cards
