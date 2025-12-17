"""SQL Agent for converting natural language to SQL queries."""

from typing import Optional, Tuple
from langchain_core.prompts import ChatPromptTemplate

from src.agents.base import BaseAgent, AgentState
from src.config import Config
from src.utils.database import DatabaseManager
from src.utils.llm_factory import get_llm
from src.utils.cache_manager import DataCacheManager


class SQLAgent(BaseAgent):
    """Agent that converts natural language to SQL and executes queries."""
    
    def __init__(self, config: Config, smart_limit: bool = True, smart_limit_rows: int = 1000):
        """Initialize SQL Agent.
        
        Args:
            config: Configuration object
            smart_limit: If True, automatically add LIMIT to queries without one
            smart_limit_rows: Default LIMIT value to add
        """
        super().__init__(config=config, name="sql_agent", 
                        description="Converts natural language queries to SQL and retrieves data")
        self.llm = get_llm()
        self.db_manager = DatabaseManager()
        self.cache_manager = DataCacheManager(config)
        self.smart_limit = smart_limit
        self.smart_limit_rows = smart_limit_rows
    
    def execute(self, state: AgentState) -> AgentState:
        """Execute SQL query generation and data retrieval.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with query results
        """
        # Use retry wrapper for execution
        return self.execute_with_retry(state, self._execute_impl)
    
    def _execute_impl(self, state: AgentState) -> AgentState:
        """Implementation of SQL agent execution (wrapped in retry logic)."""
        try:
            # Add to agent chain
            state.agent_chain.append("sql_agent")
            
            # Get database schema for context
            schema_info = self.db_manager.get_schema_info()
            
            # Add pinned tables info if available
            pinned_tables_info = state.metadata.get('pinned_tables_schema', '')
            if pinned_tables_info:
                schema_info += f"\n\n{pinned_tables_info}"
            
            # Generate SQL query using LLM (with context from previous query if available)
            sql_query = self._generate_sql_query(state.query, schema_info, state.last_sql_query)
            
            # Validate SQL for security
            is_safe, validation_msg = self._validate_sql_safety(sql_query)
            if not is_safe:
                error_msg = f"SQL Security Validation Failed: {validation_msg}"
                state.errors.append(error_msg)
                print(f"[SQL Agent] ⚠️ {error_msg}")
                print(f"[SQL Agent] Blocked query: {sql_query[:200]}")
                raise ValueError(validation_msg)
            
            # Apply smart limit if enabled
            if self.smart_limit:
                sql_query = self._apply_smart_limit(sql_query)
            
            state.sql_query = sql_query
            
            # Execute query
            results = self.db_manager.execute_query(sql_query)
            state.query_results = results
            
            # Smart caching with size limits
            cached_data, cache_msg = self.cache_manager.cache_data(results, sql_query)
            
            if cached_data is not None:
                state.cached_dataframe = cached_data
                state.last_sql_query = sql_query
                
                # Store cache metadata
                cache_info = self.cache_manager.get_cache_info()
                state.metadata['cache_info'] = cache_info
                
                print(f"[SQL Agent] Generated query: {sql_query[:100]}...")
                print(f"[SQL Agent] Retrieved {len(results) if hasattr(results, '__len__') else 'N/A'} results")
                print(f"[SQL Agent] Cache: {cache_msg}")
                
                # Warning if sampled
                if cache_info.get('is_sampled'):
                    print(f"[SQL Agent] ⚠️  Large dataset sampled: {cache_info['row_count']}/{cache_info['original_row_count']} rows cached")
            else:
                # Caching disabled or data too large
                state.cached_dataframe = None
                state.last_sql_query = sql_query
                print(f"[SQL Agent] Generated query: {sql_query[:100]}...")
                print(f"[SQL Agent] Retrieved {len(results) if hasattr(results, '__len__') else 'N/A'} results")
                print(f"[SQL Agent] Cache: {cache_msg}")
            
        except Exception as e:
            # Re-raise so retry logic can handle it
            raise
        
        return state
    
    def _generate_sql_query(self, user_query: str, schema_info: str, previous_query: str = None) -> str:
        """Generate SQL query from natural language.
        
        Args:
            user_query: User's natural language query
            schema_info: Database schema information
            previous_query: Previous SQL query for context (optional)
            
        Returns:
            SQL query string
        """
        # Fast path for common metadata queries
        query_lower = user_query.lower()
        if any(pattern in query_lower for pattern in ['show tables', 'list tables', 'what tables', 'all tables']):
            return "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name;"
        
        if 'show columns' in query_lower or 'list columns' in query_lower:
            # Try to extract table name
            import re
            match = re.search(r'(?:in|from|for)\s+(\w+)', query_lower)
            if match:
                table_name = match.group(1)
                return f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position;"
        
        # Build context section if previous query exists
        context_section = ""
        if previous_query:
            context_section = f"""
Previous Query Context:
The user previously executed this query:
{previous_query}

IMPORTANT: When the user asks to "convert", "format", "transform", "change", or "update" data:
- Modify the PREVIOUS QUERY, not a new table
- Extract table names and columns from the previous query
- Apply the transformation to those specific columns
- Preserve the table context from the previous query
"""
        
        system_message = """You are an expert SQL query generator. Generate valid, executable SQL queries from natural language.

Database Schema:
{schema}
""" + context_section + """
CRITICAL RULES:
1. Output ONLY the complete SQL query - nothing else
2. NO markdown, NO code blocks, NO explanations
3. Query must be syntactically correct and executable
4. All strings must be properly quoted with matching quotes
5. ONLY generate SELECT or WITH queries (READ-ONLY operations)
6. NEVER generate DELETE, DROP, INSERT, UPDATE, TRUNCATE, ALTER, or any data-modifying operations
7. Do NOT include SQL comments (--) or multiple statements (;;)

For metadata queries:
- List tables: SELECT table_name FROM information_schema.tables WHERE table_schema = 'main';
- Describe table: SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tablename';

For data queries:
- ALWAYS JOIN dimension tables to get meaningful names instead of IDs
  * Customer IDs → join with customer/customer_demographics for names, demographics
  * Date keys (date_sk, sold_date_sk, returned_date_sk) → join with date_dim for actual dates
  * Item/Product IDs → join with item for product names, categories
  * Store IDs → join with store for store names, locations
  * Time IDs → join with time_dim for time values
- Example: Instead of "SELECT customer_sk FROM sales", use "SELECT c.customer_id, c.first_name, c.last_name FROM sales s JOIN customer c ON s.customer_sk = c.customer_sk"
- Use proper JOINs to enrich data with human-readable values
- Add WHERE clauses for filtering
- Include ORDER BY for sorting
- Add LIMIT for large result sets (default LIMIT 100)

SECURITY: You are operating in read-only mode. Any attempt to modify data will be blocked.

Output ONLY the SQL query."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("user", "Query: {question}\n\nSQL:")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            schema=schema_info,
            question=user_query
        ))
        
        # Clean up the SQL query
        sql_query = response.content.strip()
        
        # Remove markdown code blocks if present
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        elif sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        sql_query = sql_query.strip()
        
        # Remove any text after semicolon (comments or explanations)
        if ';' in sql_query:
            sql_query = sql_query.split(';')[0].strip() + ';'
        
        # Validate query has matching quotes
        single_quotes = sql_query.count("'")
        if single_quotes % 2 != 0:
            # Try to fix by adding closing quote if it's at the end
            if sql_query.count("'") > 0:
                # Simple fix: if query ends without closing quote, add it
                if not sql_query.rstrip().endswith("'") and not sql_query.rstrip().endswith(";"):
                    sql_query = sql_query.rstrip() + "'"
        
        return sql_query
    
    def _validate_sql_safety(self, sql_query: str) -> Tuple[bool, str]:
        """Validate SQL query for security risks.
        
        Args:
            sql_query: SQL query to validate
            
        Returns:
            Tuple of (is_safe: bool, message: str)
        """
        if not sql_query or not sql_query.strip():
            return False, "Empty or whitespace-only query"
        
        query_upper = sql_query.upper().strip()
        
        # Dangerous keywords that modify or delete data
        dangerous_operations = [
            'DELETE ', 'DROP ', 'TRUNCATE ', 'ALTER ', 'CREATE ',
            'INSERT ', 'UPDATE ', 'REPLACE ', 'RENAME ', 'GRANT ',
            'REVOKE ', 'EXECUTE ', 'EXEC ', 'CALL '
        ]
        
        for operation in dangerous_operations:
            if operation in query_upper:
                return False, f"Dangerous operation detected: {operation.strip()}"
        
        # Check for SQL injection patterns
        # Note: UNION is allowed if query starts with SELECT/WITH (legitimate use case)
        # but blocked if combined with dangerous patterns
        injection_patterns = [
            '--',  # SQL comments
            '/*',  # Multi-line comments
            '*/',
            '; DROP',
            '; DELETE',
            '; UPDATE',
            '; INSERT',
            'XP_CMDSHELL',  # SQL Server command execution
            'DBMS_JAVA',  # Oracle Java execution
            'UTL_FILE',  # Oracle file operations
            'INTO OUTFILE',  # MySQL file write
            'INTO DUMPFILE',
            'LOAD_FILE',  # MySQL file read
        ]
        
        for pattern in injection_patterns:
            if pattern in query_upper:
                return False, f"Potential SQL injection pattern detected: {pattern}"
        
        # Check for UNION injection specifically (after dangerous statements)
        # UNION is safe if used legitimately, but dangerous if trying to inject data
        if 'UNION' in query_upper:
            # Check if UNION appears after suspicious patterns
            if any(dangerous in query_upper for dangerous in [
                'WHERE 1=1', 'WHERE 1 =1', 'WHERE TRUE',
                "' OR '", '" OR "', "' OR 1=1", '" OR 1=1',
                "' OR TRUE", '" OR TRUE'
            ]):
                return False, "Potential SQL injection via UNION detected"
        
        # Must start with SELECT for read-only operations
        if not query_upper.startswith('SELECT') and not query_upper.startswith('WITH'):
            return False, "Only SELECT queries are allowed (query must start with SELECT or WITH)"
        
        # Check for suspicious semicolons (multiple statements)
        semicolon_count = sql_query.count(';')
        if semicolon_count > 1:
            return False, "Multiple SQL statements detected (only single queries allowed)"
        
        return True, "Query validated successfully"
    
    def _apply_smart_limit(self, sql_query: str) -> str:
        """Add LIMIT clause to query if not present.
        
        Args:
            sql_query: Original SQL query
            
        Returns:
            SQL query with LIMIT added if needed
        """
        # If smart limit is disabled, return query as-is
        if not self.smart_limit:
            return sql_query
        
        query_upper = sql_query.upper().strip()
        
        # Skip if query already has LIMIT or TOP
        if 'LIMIT' in query_upper or 'TOP ' in query_upper:
            return sql_query
        
        # Skip metadata queries
        if 'INFORMATION_SCHEMA' in query_upper:
            return sql_query
        
        # Skip aggregate-only queries (no raw data)
        if 'COUNT(*)' in query_upper and 'GROUP BY' not in query_upper:
            return sql_query
        
        # Add LIMIT before semicolon or at end
        sql_clean = sql_query.strip()
        if sql_clean.endswith(';'):
            return f"{sql_clean[:-1]} LIMIT {self.smart_limit_rows};"
        else:
            return f"{sql_clean} LIMIT {self.smart_limit_rows}"
