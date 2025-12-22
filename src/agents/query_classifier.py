"""
Query Classification System for Hybrid Agent Routing

This module implements a 3-tier classification system:
- Tier 1: Fast regex pattern matching (~95% queries, <1ms)
- Tier 2: Keyword scoring with confidence (~4% queries, <10ms)
- Tier 3: LLM-based fallback (~1% queries, ~500ms)

The goal is to minimize LLM calls while maintaining high routing accuracy.
"""

import re
from enum import Enum
from typing import Tuple, Dict, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from src.config import Config
from src.utils.llm_factory import get_llm


class PlanType(str, Enum):
    """Types of execution plans for different query patterns."""
    SQL_ONLY = "sql_only"  # Just execute SQL and return results
    SQL_ANALYSIS = "sql_analysis"  # SQL + statistical analysis
    SQL_VIZ = "sql_viz"  # SQL + visualization
    SQL_ANALYSIS_VIZ = "sql_analysis_viz"  # SQL + analysis + visualization
    SQL_PROFILING = "sql_profiling"  # SQL + data profiling/EDA
    SQL_PREPROCESSING = "sql_preprocessing"  # SQL + profiling + preprocessing
    SQL_MODELING = "sql_modeling"  # SQL + profiling + preprocessing + modeling


class QueryPlan(BaseModel):
    """Structured output from LLM classifier."""
    plan_type: PlanType = Field(description="The execution plan type")
    reasoning: str = Field(description="Brief explanation of the classification")
    confidence: float = Field(description="Confidence score between 0 and 1")


class QueryClassifier:
    """Hybrid query classifier with 3-tier routing."""
    
    # Follow-up query patterns (reuse data)
    FOLLOWUP_PATTERNS = [
        r'\b(this|that|the|same)\s+(data|dataset|table|results?)\b',
        r'\b(these|those)\s+(rows|records|entries)\b',
        r'\b(from\s+)?(above|previous|last|earlier)\b',
        r'\bnow\s+(analyze|plot|chart|show|visualize)\b',
        r'\b(also|additionally)\s+(analyze|plot|show|create)\b',
        r'\b(what|explain)\s+(is|does|means?)\s+(this|that|the)\b',
        r'^\d+\s+(what|how|why|explain)',  # Starts with number like "2451521 what..."
        r'\bthis\s+(\w+\s+)?(format|value|number|code)\b',
        r'\b(original|first|initial)\s+(data|dataset|table|query|results?)\b',  # Reference to original data
        r'\b(step|query|turn)\s+(\d+)\b',  # "from step 2", "query 1"
        r'\b(first|second|third|earlier)\s+(chart|graph|plot|visualization)\b',  # Reference to specific viz
        r'\bconvert\s+(this|that|the)\s+',
    ]
    
    # Visualization update patterns
    VIZ_UPDATE_PATTERNS = [
        r'\b(add|update|change|modify|adjust)\s+(the\s+)?(label|title|axis|legend|color)\b',
        r'\b(make|set)\s+(the\s+)?(x|y)\s*-?\s*axis\b',
        r'\bchange\s+(to|into)\s+a\s+(bar|line|pie|scatter)\b',
        r'\b(bigger|smaller|larger|wider|taller)\s+(chart|plot|graph|figure)\b',
    ]
    
    # Tier 1: Regex patterns for common metadata queries
    METADATA_PATTERNS = [
        r'\b(show|list|display|what)\s+(tables?|columns?|schema|structure)\b',
        r'\b(describe|explain)\s+(table|database|schema)\b',
        r'\bshow\s+me\s+(what|all|the)\s+(tables?|data)\b',
        r'\bwhat\s+(tables?|columns?)\s+(are|do\s+I\s+have|exist)\b',
        r'\btable\s+(names?|list|schema)\b',
        r'\bschema\s+(information|details|structure)\b',
    ]
    
    # Patterns for queries that need visualization
    VIZ_PATTERNS = [
        r'\b(plot|chart|graph|visuali[sz]e|show\s+me\s+a\s+(chart|graph|plot))\b',
        r'\b(bar\s+chart|line\s+chart|pie\s+chart|scatter\s+plot|histogram)\b',
        r'\b(trend|distribution|comparison)\s+(over\s+time|by|across)\b',
        r'\bdraw\s+(a\s+)?(chart|graph|plot)\b',
    ]
    
    # Patterns for queries needing statistical analysis
    ANALYSIS_PATTERNS = [
        r'\b(analy[sz]e|statistics?|statistical|correlat(ion|e)|trend)\b',
        r'\b(mean|median|mode|std|variance|percentile|quartile)\b',
        r'\b(compare|comparison|difference|change|growth|decline)\b',
        r'\b(pattern|anomaly|outlier|insight|finding)\b',
        r'\bwhat\s+(does\s+this\s+mean|can\s+you\s+tell\s+me|insights?)\b',
    ]
    
    # Patterns for data profiling / EDA (exploratory data analysis)
    PROFILING_PATTERNS = [
        r'\b(profil(e|ing)|EDA|exploratory\s+data\s+analysis|data\s+exploration?)\b',
        r'\b(explore|inspect|examine|understand)\s+(the\s+)?(data|dataset)\b',
        r'\b(data\s+quality|missing\s+values?|null\s+values?|duplicates?)\b',
        r'\b(summary\s+statistics|descriptive\s+statistics|data\s+overview)\b',
        r'\b(check|assess|review)\s+(data|dataset|quality)\b',
    ]
    
    # Patterns for preprocessing / feature engineering
    PREPROCESSING_PATTERNS = [
        r'\b(preprocess(ing)?|feature\s+engineering|transformation|transform)\b',
        r'\b(clean(ing)?|prepare|preparation)\s+(the\s+)?(data|dataset)\b',
        r'\b(encod(e|ing)|scaling|normali[sz]ation|standardi[sz]ation)\b',
        r'\b(handle|impute|fill)\s+(missing|null)\s+(values?|data)\b',
        r'\b(remove|drop)\s+(duplicates?|outliers?|missing\s+values?)\b',
        r'\b(create|engineer|generate)\s+(features?|variables?)\b',
    ]
    
    # Patterns for predictive modeling / machine learning
    MODELING_PATTERNS = [
        r'\b(build|train|create|fit)\s+(a\s+)?(model|classifier|regressor)\b',
        r'\b(predict|forecast|estimate)\s+',
        r'\b(machine\s+learning|ML|predictive\s+model(ing)?)\b',
        r'\b(random\s+forest|decision\s+tree|logistic\s+regression|linear\s+regression)\b',
        r'\b(xgboost|gradient\s+boosting|neural\s+network|deep\s+learning)\b',
        r'\b(classification|regression|clustering)\s+(model|task|problem)\b',
        r'\b(churn|fraud|recommendation)\s+(prediction|model|detection)\b',
        r'\b(model\s+performance|model\s+evaluation|cross[-\s]validation)\b',
    ]
    
    # Keywords with weights for Tier 2 scoring
    KEYWORD_WEIGHTS = {
        # SQL-only indicators (high weight)
        'show': 0.3, 'list': 0.3, 'display': 0.25, 'get': 0.25,
        'table': 0.3, 'schema': 0.35, 'column': 0.3, 'describe': 0.35,
        
        # Visualization indicators
        'plot': 0.8, 'chart': 0.8, 'graph': 0.8, 'visualize': 0.9,
        'trend': 0.6, 'distribution': 0.6, 'histogram': 0.7,
        
        # Analysis indicators
        'analyze': 0.8, 'analysis': 0.8, 'statistics': 0.7, 'statistical': 0.7,
        'correlation': 0.75, 'pattern': 0.6, 'insight': 0.7, 'compare': 0.6,
        'mean': 0.5, 'median': 0.5, 'variance': 0.6, 'anomaly': 0.7,
        
        # Profiling / EDA indicators
        'profile': 0.85, 'profiling': 0.85, 'eda': 0.9, 'exploratory': 0.8,
        'explore': 0.75, 'exploration': 0.8, 'inspect': 0.7, 'examine': 0.7,
        'quality': 0.65, 'overview': 0.6, 'summary': 0.5, 'descriptive': 0.6,
        
        # Preprocessing / Feature Engineering indicators
        'preprocess': 0.85, 'preprocessing': 0.85, 'feature': 0.75, 'engineering': 0.75,
        'transformation': 0.8, 'transform': 0.8, 'clean': 0.7, 'cleaning': 0.7,
        'prepare': 0.7, 'preparation': 0.7, 'encode': 0.75, 'encoding': 0.75,
        'scaling': 0.75, 'normalization': 0.75, 'standardization': 0.75,
        'impute': 0.8, 'imputation': 0.8,
        
        # Modeling / ML indicators
        'predict': 0.9, 'prediction': 0.9, 'forecast': 0.85, 'model': 0.8,
        'train': 0.75, 'build': 0.6, 'classify': 0.85, 'classification': 0.85,
        'regression': 0.85, 'clustering': 0.85, 'machine': 0.7, 'learning': 0.7,
        'churn': 0.8, 'fraud': 0.8, 'recommendation': 0.75,
    }
    
    def __init__(self, config: Config):
        """Initialize the classifier with configuration."""
        self.config = config
        self.llm = None  # Lazy initialization for Tier 3
        self._compiled_patterns = {
            'followup': [re.compile(p, re.IGNORECASE) for p in self.FOLLOWUP_PATTERNS],
            'viz_update': [re.compile(p, re.IGNORECASE) for p in self.VIZ_UPDATE_PATTERNS],
            'metadata': [re.compile(p, re.IGNORECASE) for p in self.METADATA_PATTERNS],
            'viz': [re.compile(p, re.IGNORECASE) for p in self.VIZ_PATTERNS],
            'analysis': [re.compile(p, re.IGNORECASE) for p in self.ANALYSIS_PATTERNS],
            'profiling': [re.compile(p, re.IGNORECASE) for p in self.PROFILING_PATTERNS],
            'preprocessing': [re.compile(p, re.IGNORECASE) for p in self.PREPROCESSING_PATTERNS],
            'modeling': [re.compile(p, re.IGNORECASE) for p in self.MODELING_PATTERNS],
        }
    
    def is_followup_query(self, query: str) -> bool:
        """Check if query references previous data/context."""
        return any(p.search(query) for p in self._compiled_patterns['followup'])
    
    def is_viz_update_query(self, query: str) -> bool:
        """Check if query is updating existing visualization."""
        return any(p.search(query) for p in self._compiled_patterns['viz_update'])
    
    def extract_snapshot_reference(self, query: str) -> Tuple[bool, int]:
        """Extract snapshot reference from query (e.g., 'from step 2', 'original data').
        
        Args:
            query: User's natural language query
            
        Returns:
            Tuple of (has_reference, snapshot_id)
            - has_reference: True if query references a specific snapshot
            - snapshot_id: The snapshot ID (1 for 'original'/'first', otherwise extracted number)
        """
        query_lower = query.lower()
        
        # Check for explicit step/query number references
        step_match = re.search(r'\b(step|query|turn)\s+(\d+)\b', query_lower)
        if step_match:
            return True, int(step_match.group(2))
        
        # Check for ordinal references (first, second, third)
        ordinal_map = {'first': 1, 'second': 2, 'third': 3}
        for ordinal, num in ordinal_map.items():
            if re.search(rf'\b{ordinal}\s+(data|dataset|table|query|results?|chart|graph|plot|visualization)\b', query_lower):
                return True, num
        
        # Check for 'original' or 'initial' references (maps to snapshot 1)
        if re.search(r'\b(original|initial)\s+(data|dataset|table|query|results?)\b', query_lower):
            return True, 1
        
        return False, 0
    
    def classify_query(self, query: str, has_cached_data: bool = False) -> Tuple[PlanType, float, Dict[str, bool]]:
        """
        Classify a query using 3-tier hybrid approach with context awareness.
        
        Args:
            query: User's natural language query
            has_cached_data: Whether there's cached data from previous query
            
        Returns:
            Tuple of (PlanType, confidence_score, context_flags)
            context_flags: {'reuse_data': bool, 'update_viz': bool}
        """
        context_flags = {
            'reuse_data': False,
            'update_viz': False
        }
        
        # Check for follow-up queries that can reuse data
        if has_cached_data and self.is_followup_query(query):
            context_flags['reuse_data'] = True
        
        # Check for visualization update queries
        if self.is_viz_update_query(query):
            context_flags['update_viz'] = True
            # If updating viz, we likely need cached data
            if has_cached_data:
                context_flags['reuse_data'] = True
        
        # Tier 1: Fast regex matching
        tier1_result = self._tier1_regex_match(query)
        if tier1_result:
            return (*tier1_result, context_flags)
        
        # Tier 2: Keyword scoring
        tier2_result = self._tier2_keyword_scoring(query)
        if tier2_result:
            return (*tier2_result, context_flags)
        
        # Tier 3: LLM fallback
        llm_result = self._tier3_llm_classify(query)
        return (*llm_result, context_flags)
    
    def _tier1_regex_match(self, query: str) -> Tuple[PlanType, float] | None:
        """
        Tier 1: Fast regex pattern matching for common queries.
        Returns (PlanType, 1.0) if matched, None otherwise.
        """
        # Check metadata patterns (SQL_ONLY)
        for pattern in self._compiled_patterns['metadata']:
            if pattern.search(query):
                return (PlanType.SQL_ONLY, 1.0)
        
        # Check for different analysis types
        has_viz = any(p.search(query) for p in self._compiled_patterns['viz'])
        has_analysis = any(p.search(query) for p in self._compiled_patterns['analysis'])
        has_profiling = any(p.search(query) for p in self._compiled_patterns['profiling'])
        has_preprocessing = any(p.search(query) for p in self._compiled_patterns['preprocessing'])
        has_modeling = any(p.search(query) for p in self._compiled_patterns['modeling'])
        
        # Determine plan based on what's detected (priority order: modeling > preprocessing > profiling)
        if has_modeling:
            # Modeling requires full pipeline: SQL → profiling → preprocessing → modeling
            return (PlanType.SQL_MODELING, 0.95)
        elif has_preprocessing:
            # Preprocessing requires: SQL → profiling → preprocessing
            return (PlanType.SQL_PREPROCESSING, 0.95)
        elif has_profiling:
            # Profiling requires: SQL → profiling
            return (PlanType.SQL_PROFILING, 0.95)
        elif has_viz and has_analysis:
            return (PlanType.SQL_ANALYSIS_VIZ, 0.95)
        elif has_viz:
            return (PlanType.SQL_VIZ, 0.95)
        elif has_analysis:
            return (PlanType.SQL_ANALYSIS, 0.95)
        
        return None
    
    def _tier2_keyword_scoring(self, query: str) -> Tuple[PlanType, float] | None:
        """
        Tier 2: Keyword-based scoring with confidence threshold.
        Returns (PlanType, confidence) if confidence > 0.85, None otherwise.
        """
        query_lower = query.lower()
        words = re.findall(r'\b\w+\b', query_lower)
        
        # Calculate weighted scores for different plan types
        viz_score = 0.0
        analysis_score = 0.0
        metadata_score = 0.0
        profiling_score = 0.0
        preprocessing_score = 0.0
        modeling_score = 0.0
        
        for word in words:
            if word in self.KEYWORD_WEIGHTS:
                weight = self.KEYWORD_WEIGHTS[word]
                
                # Categorize keyword by type
                if word in ['plot', 'chart', 'graph', 'visualize', 'trend', 'distribution', 'histogram']:
                    viz_score += weight
                elif word in ['predict', 'prediction', 'forecast', 'model', 'train', 'build', 
                              'classify', 'classification', 'regression', 'clustering', 'machine', 
                              'learning', 'churn', 'fraud', 'recommendation']:
                    modeling_score += weight
                elif word in ['preprocess', 'preprocessing', 'feature', 'engineering', 'transformation',
                              'transform', 'clean', 'cleaning', 'prepare', 'preparation', 'encode',
                              'encoding', 'scaling', 'normalization', 'standardization', 'impute', 'imputation']:
                    preprocessing_score += weight
                elif word in ['profile', 'profiling', 'eda', 'exploratory', 'explore', 'exploration',
                              'inspect', 'examine', 'quality', 'overview', 'summary', 'descriptive']:
                    profiling_score += weight
                elif word in ['analyze', 'analysis', 'statistics', 'statistical', 'correlation', 
                              'pattern', 'insight', 'compare', 'mean', 'median', 'variance', 'anomaly']:
                    analysis_score += weight
                elif word in ['show', 'list', 'display', 'get', 'table', 'schema', 'column', 'describe']:
                    metadata_score += weight
        
        # Determine plan type based on highest scores (with threshold)
        threshold = 0.85
        
        # Priority: modeling > preprocessing > profiling > viz+analysis > viz > analysis > metadata
        if modeling_score > 1.0:  # Modeling keywords have high weights (0.75-0.9)
            return (PlanType.SQL_MODELING, min(0.95, modeling_score / 2.0))
        elif preprocessing_score > 1.0:
            return (PlanType.SQL_PREPROCESSING, min(0.95, preprocessing_score / 2.0))
        elif profiling_score > 1.0:
            return (PlanType.SQL_PROFILING, min(0.95, profiling_score / 2.0))
        
        # Legacy scoring for viz/analysis combinations
        total_score = viz_score + analysis_score + metadata_score
        if total_score == 0:
            return None
        
        viz_confidence = viz_score / total_score
        analysis_confidence = analysis_score / total_score
        metadata_confidence = metadata_score / total_score
        
        if metadata_confidence > threshold:
            return (PlanType.SQL_ONLY, metadata_confidence)
        
        if viz_confidence > 0.4 and analysis_confidence > 0.4:
            confidence = min(viz_confidence + analysis_confidence, 0.95)
            return (PlanType.SQL_ANALYSIS_VIZ, confidence)
        
        if viz_confidence > threshold:
            return (PlanType.SQL_VIZ, viz_confidence)
        
        if analysis_confidence > threshold:
            return (PlanType.SQL_ANALYSIS, analysis_confidence)
        
        return None
    
    def _tier3_llm_classify(self, query: str) -> Tuple[PlanType, float]:
        """
        Tier 3: LLM-based classification with structured output.
        Fallback for ambiguous queries that fail Tier 1 and Tier 2.
        """
        # Lazy initialize LLM
        if self.llm is None:
            self.llm = get_llm()
        
        # Create parser for structured output
        parser = PydanticOutputParser(pydantic_object=QueryPlan)
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a query classifier for a data analytics system. 
Analyze the user's query and determine what type of processing is needed.

Plan Types:
- sql_only: Simple data retrieval, metadata queries, table listings
- sql_analysis: Queries needing statistical analysis, insights, patterns, comparisons
- sql_viz: Queries needing visual output (charts, graphs, plots)
- sql_analysis_viz: Queries needing both analysis and visualization
- sql_profiling: Data quality checks, profiling, data assessment (runs profiling → communication)
- sql_preprocessing: Data cleaning, transformation, feature engineering (runs profiling → preprocessing → communication)
- sql_modeling: Predictive modeling, machine learning tasks (runs profiling → preprocessing → modeling → communication)

Priority Rules:
1. If query involves ML/prediction/classification → sql_modeling
2. If query involves data transformation/cleaning/feature engineering → sql_preprocessing
3. If query involves data quality assessment/profiling → sql_profiling
4. Otherwise use original plan types (sql_only, sql_analysis, sql_viz, sql_analysis_viz)

Consider:
- ML keywords: predict, forecast, classify, train, model → sql_modeling
- Preprocessing keywords: clean, transform, encode, scale, impute → sql_preprocessing
- Profiling keywords: data quality, assess data, check issues → sql_profiling
- Explicit requests (e.g., "show me a chart" → sql_viz)
- Implicit needs (e.g., "compare trends" → sql_analysis_viz)
- Simple lookups (e.g., "list tables" → sql_only)

{format_instructions}"""),
            ("user", "Query: {query}")
        ])
        
        # Create chain
        chain = prompt | self.llm | parser
        
        try:
            result: QueryPlan = chain.invoke({
                "query": query,
                "format_instructions": parser.get_format_instructions()
            })
            return (result.plan_type, result.confidence)
        except Exception as e:
            # Fallback to safe default
            print(f"LLM classification failed: {e}")
            return (PlanType.SQL_ANALYSIS, 0.5)


def classify_query(query: str, config: Config = None) -> Tuple[PlanType, float]:
    """
    Convenience function for query classification.
    
    Args:
        query: User's natural language query
        config: Configuration object (creates default if None)
        
    Returns:
        Tuple of (PlanType, confidence_score)
    """
    if config is None:
        config = Config()
    
    classifier = QueryClassifier(config)
    return classifier.classify_query(query)
