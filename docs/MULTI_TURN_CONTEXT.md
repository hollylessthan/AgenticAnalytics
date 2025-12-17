# Multi-Turn Context Preservation

## Problem Statement

Previously, the system only stored the **most recent** query result (DataFrame, SQL query, visualization). This caused issues:

1. **Lost context on errors**: If a query returns no results (wrong filter), previous visualizations disappear
2. **No reference to earlier data**: Can't drill down on original data after intermediate transformations
3. **Single-turn memory**: Can't reference "data from step 2" or "original table"

## Solution: Dual Approach

### Approach 1: Conversation Snapshots (Automatic)

**Implementation**: Store last N (default 10) conversation turns with full context

**Components**:
- `ConversationSnapshot` class: Stores query, SQL, DataFrame, visualization path/code, response, timestamp, snapshot_id
- `AgentState.state_history`: List of snapshots, auto-trimmed to `max_history_size`
- `AgentState.add_snapshot()`: Creates snapshot after each successful query
- `AgentState.get_snapshot(id)`: Retrieve specific snapshot by ID
- `AgentState.referenced_snapshot_id`: Tracks which snapshot is being referenced

**Snapshot Reference Detection**:
```python
# Query classifier extracts references:
"use data from step 2"  → snapshot_id=2
"based on original data" → snapshot_id=1
"drill down first table" → snapshot_id=1
"from query 3"           → snapshot_id=3
```

**Query patterns detected**:
- Explicit: `step 2`, `query 1`, `turn 3`
- Ordinal: `first data`, `second chart`, `third query`
- Semantic: `original data`, `initial table`

**Workflow**:
1. User asks: "show me sales data"
   - Snapshot #1 created with DataFrame, SQL, response
2. User asks: "filter for 2023" (returns empty - wrong year)
   - Snapshot #2 created (empty data)
3. User asks: "use original data and filter for 2003"
   - System detects "original data" → loads snapshot #1
   - Runs new query with correct filter
   - Snapshot #3 created

### Approach 2: Pinned Tables (Manual User Control)

**Implementation**: User can "pin" any DataFrame as a permanent table in session

**Components**:
- `SessionTableManager`: Manages pinned tables in DuckDB session
- `PinnedTable`: Metadata (name, row_count, columns, created_at, original_query)
- UI: "📌 Pin as Table" button on every DataFrame result
- Sidebar: View all pinned tables, rename, delete, preview

**Features**:
- Tables stored as `pinned_table_1`, `pinned_table_2`, or custom names like `pinned_sales_2003`
- Included in schema info for SQL agent (LLM knows about them)
- Persist for entire session (until manually deleted or session ends)
- Can query pinned tables by name: "join pinned_table_1 with store_sales"

**Workflow**:
1. User: "get customer returns for top 100 customers"
   - Data shown, user clicks "📌 Pin as Table"
   - Saved as `pinned_table_1`
2. User: "show sales for same customers"
   - Can ask: "join pinned_table_1 with store_sales on customer_sk"
   - SQL agent includes pinned tables in schema, generates correct JOIN

## Code Changes

### 1. Core State Management (`src/agents/base.py`)

**New Classes**:
```python
class ConversationSnapshot(BaseModel):
    timestamp: datetime
    query: str
    sql_query: Optional[str]
    dataframe: Optional[Any]  # Stored in memory
    visualization_path: Optional[str]
    visualization_code: Optional[str]
    response: Optional[str]
    snapshot_id: int  # Sequential: 1, 2, 3...
```

**Enhanced AgentState**:
```python
# New fields
state_history: List[ConversationSnapshot] = Field(default_factory=list)
max_history_size: int = Field(default=10)
referenced_snapshot_id: Optional[int] = None

# Helper methods
def add_snapshot() -> None:
    """Create snapshot and trim to max_history_size"""
    
def get_snapshot(snapshot_id: int) -> Optional[ConversationSnapshot]:
    """Retrieve specific snapshot"""
    
def get_latest_snapshot() -> Optional[ConversationSnapshot]:
    """Get most recent snapshot"""
```

### 2. Session Table Manager (`src/utils/session_tables.py`)

**New Module** for pinned table management:

```python
class SessionTableManager:
    def pin_dataframe(df, original_query, custom_name) -> str:
        """Create temp table in DuckDB from DataFrame"""
    
    def list_pinned_tables() -> List[Dict]:
        """Get all pinned table metadata"""
    
    def get_table_preview(table_name, limit=5) -> pd.DataFrame:
        """Preview pinned table data"""
    
    def rename_table(old_name, new_name) -> bool:
        """Rename pinned table"""
    
    def drop_table(table_name) -> bool:
        """Delete pinned table"""
    
    def clear_all() -> None:
        """Drop all pinned tables"""
    
    def get_schema_info() -> str:
        """Format schema for LLM prompt"""
```

### 3. Query Classifier (`src/agents/query_classifier.py`)

**New Patterns**:
```python
FOLLOWUP_PATTERNS = [
    # ... existing patterns ...
    r'\b(original|first|initial)\s+(data|dataset|table|query|results?)\b',
    r'\b(step|query|turn)\s+(\d+)\b',
    r'\b(first|second|third|earlier)\s+(chart|graph|plot|visualization)\b',
]
```

**New Method**:
```python
def extract_snapshot_reference(query: str) -> Tuple[bool, int]:
    """Extract snapshot ID from query.
    
    Returns:
        (has_reference, snapshot_id)
        
    Examples:
        "use step 2 data" → (True, 2)
        "original table" → (True, 1)
        "show chart" → (False, 0)
    """
```

### 4. Orchestrator (`src/agents/orchestrator.py`)

**Enhanced _classify_query()**:
```python
# Check for snapshot references
has_reference, snapshot_id = self.classifier.extract_snapshot_reference(state.query)
if has_reference and state.state_history:
    snapshot = state.get_snapshot(snapshot_id)
    if snapshot and snapshot.dataframe is not None:
        # Restore data from snapshot
        state.cached_dataframe = snapshot.dataframe
        state.last_sql_query = snapshot.sql_query
        state.referenced_snapshot_id = snapshot_id
```

### 5. SQL Agent (`src/agents/sql_agent.py`)

**Schema Enhancement**:
```python
# Get database schema
schema_info = self.db_manager.get_schema_info()

# Add pinned tables info from metadata
pinned_tables_info = state.metadata.get('pinned_tables_schema', '')
if pinned_tables_info:
    schema_info += f"\n\n{pinned_tables_info}"
```

**Previous Query Context** (also fixed):
```python
# Build context section if previous query exists
context_section = ""
if previous_query:
    context_section = f"""
Previous Query Context:
{previous_query}

IMPORTANT: When user asks to "convert", "format", "transform" data:
- Modify the PREVIOUS QUERY, not a new table
- Extract table names and columns from previous query
"""

system_message = """...""" + context_section + """..."""
```

### 6. UI Updates (`src/app.py`)

**Initialization**:
```python
# Initialize table manager with DB connection
if st.session_state.orchestrator:
    sql_agent = st.session_state.orchestrator.sql_agent
    st.session_state.table_manager = SessionTableManager(sql_agent.db)
```

**Snapshot Creation**:
```python
# After orchestrator.run()
result.add_snapshot()  # Auto-create snapshot
st.session_state.previous_state = result  # Includes full state_history
```

**Pinned Tables Metadata**:
```python
# Pass pinned schema to orchestrator
metadata = {}
if st.session_state.table_manager:
    pinned_schema = st.session_state.table_manager.get_schema_info()
    if pinned_schema:
        metadata['pinned_tables_schema'] = pinned_schema

previous_state.metadata.update(metadata)
```

**Pin Button in Results**:
```python
# In display_chat_message()
if st.button("📌 Pin as Table", key=f"pin_{id(result)}"):
    table_name = st.session_state.table_manager.pin_dataframe(
        result.query_results,
        original_query=result.sql_query
    )
    st.success(f"✅ Pinned as `{table_name}`")
```

**Sidebar Management**:
```python
st.subheader("📌 Pinned Tables")

for table in pinned_tables:
    with st.expander(f"🗂️ {table['name']}"):
        # Show metadata, preview
        # Delete and rename buttons
```

## Usage Examples

### Example 1: Multi-Step Drill-Down with Snapshots

```
User: "show me top 100 customers by revenue"
→ Snapshot #1: 100 rows of customer data

User: "analyze by region"
→ Snapshot #2: grouped by region (10 rows)

User: "now drill down by state for the top customers"
→ System detects "top customers"
→ Loads Snapshot #1 (original 100 customers)
→ Snapshot #3: drill-down by state

User: "compare to query 2 data"
→ System loads Snapshot #2 (region aggregates)
→ Can compare region vs state breakdowns
```

### Example 2: Pinned Tables for Complex Joins

```
User: "get recent customer returns"
→ 50,000 rows shown
→ User clicks "📌 Pin as Table"
→ Saved as pinned_table_1

User: "now show sales for those customers in 2003"
→ User can ask: "join pinned_table_1 with store_sales on customer_sk where year=2003"
→ SQL agent sees pinned_table_1 in schema, generates correct query

User: "join pinned_table_1 with customer demographics"
→ Pinned table acts like regular database table
```

### Example 3: Error Recovery

```
User: "show sales for 2023"
→ Empty result (data only has 2003)
→ Snapshot #1: empty DataFrame

User: "ok show for 2003 instead"
→ Still references wrong context (Snapshot #1 is empty)
→ Snapshot #2: correct data for 2003

User: "create chart from step 2"
→ System detects "step 2" → loads Snapshot #2
→ Creates visualization from correct data
```

## Benefits

### Snapshot System Benefits
- **Automatic**: No user action required
- **Lightweight**: Stores 10 most recent turns (configurable)
- **Error recovery**: Can reference earlier successful queries
- **Multi-step workflows**: Drill down, compare, analyze across steps
- **Natural language**: "original data", "from step 2", "first query"

### Pinned Tables Benefits
- **User control**: Manually save important datasets
- **Persistent**: Remains until deleted or session ends
- **Queryable**: Acts as real database tables in SQL
- **Complex joins**: Can join multiple pinned tables together
- **Naming**: Custom names like `pinned_sales_q1`, `pinned_top_customers`

### Combined Power
- Use snapshots for quick "go back 2 steps" operations
- Use pinned tables for long-running analysis with stable reference data
- Mix approaches: "join pinned_table_1 with data from step 3"

## Configuration

### Snapshot Settings (AgentState)
```python
max_history_size: int = 10  # Number of snapshots to keep
```

To change: modify `AgentState` field default in `src/agents/base.py`

### Pinned Table Limits
No hard limits (constrained by DuckDB session memory), but:
- Stored as temp tables (not persisted to disk)
- Cleared when session ends
- User can manually delete via sidebar

## Testing Checklist

- [ ] Create data → drill down dimension 1 → verify cached
- [ ] Create data → drill down dimension 2 from original → verify snapshot reference works
- [ ] Query returns empty → reference "original data" → verify earlier snapshot loaded
- [ ] Pin table → query pinned table by name → verify JOIN works
- [ ] Pin 2 tables → JOIN them together → verify schema info correct
- [ ] Reference "step 2" → verify snapshot_id=2 loaded
- [ ] Reference "first chart" → verify snapshot_id=1 loaded
- [ ] Create 15 queries → verify only last 10 snapshots kept
- [ ] Rename pinned table → query by new name → verify works
- [ ] Delete pinned table → verify removed from schema info

## Future Enhancements

1. **Persistent pinned tables**: Save to disk, reload across sessions
2. **Snapshot search**: Semantic search over snapshot queries ("find the query about sales")
3. **Snapshot visualization**: Timeline UI showing all conversation turns
4. **Smart garbage collection**: Remove large DataFrames from old snapshots, keep only metadata
5. **Export snapshots**: Download entire conversation as reproducible notebook
6. **Diff visualization**: "show me what changed between step 2 and step 5"
7. **Undo/redo**: Navigate conversation like version control
8. **Named snapshots**: User can name important snapshots like pinned tables
