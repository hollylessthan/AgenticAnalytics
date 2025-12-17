## Data Caching System - Technical Details

### Architecture Overview

The caching system has **three layers of protection** against memory issues:

```
┌─────────────────────────────────────────┐
│  User Query                             │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│  SQL Agent executes query               │
│  Returns DataFrame (potentially huge)   │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│  CacheManager.cache_data()              │
│  ┌───────────────────────────────────┐  │
│  │ Layer 1: Size Check                │  │
│  │ - Check row count vs MAX_CACHE_ROWS│  │
│  │ - Check memory size vs MAX_CACHE_MB│  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ Layer 2: Auto-Sampling            │  │
│  │ - If too large AND auto-sample=true│  │
│  │ - Sample N rows randomly           │  │
│  │ - Cache sample, not full dataset  │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │ Layer 3: TTL (Time-to-Live)       │  │
│  │ - Expires after X seconds          │  │
│  │ - Auto-clears on next access       │  │
│  └───────────────────────────────────┘  │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│  Cache safely stored in memory          │
│  state.cached_dataframe = sampled_data  │
└─────────────────────────────────────────┘
```

### Where Cache Lives

**Location:** In-memory (Python process memory)
- Stored in `AgentState.cached_dataframe`
- Managed by `DataCacheManager` instance
- Per-session (cleared on app restart)

**Persistence:** None by default
- Data exists only while app is running
- Lost on restart/crash
- No disk I/O (for speed)

**Scope:**
- Single orchestrator instance
- Can share across multiple queries in same session
- Isolated between different users (if using session state)

### Safety Mechanisms

#### 1. Row Count Limit
```python
MAX_CACHE_ROWS=10000  # Default: 10,000 rows
```

**What it does:**
- Checks `len(dataframe)` before caching
- Rejects cache if exceeds limit
- Or samples if AUTO_SAMPLE_LARGE_RESULTS=true

**Example:**
```
Query returns 1,000,000 rows
MAX_CACHE_ROWS = 10,000
AUTO_SAMPLE = true
Result: Cache 10,000 random rows (1% sample)
```

#### 2. Memory Size Limit
```python
MAX_CACHE_SIZE_MB=100  # Default: 100MB
```

**What it does:**
- Calculates actual memory footprint
- Uses `DataFrame.memory_usage(deep=True)`
- More accurate than row count alone

**Why it matters:**
```
100 rows × 10 columns × 8 bytes = 8 KB (tiny)
100 rows × 1000 columns × 8 bytes = 800 KB (still small)
1M rows × 100 columns × 8 bytes = 800 MB (HUGE!)
```

#### 3. Auto-Sampling
```python
AUTO_SAMPLE_LARGE_RESULTS=true
SAMPLE_SIZE=1000
```

**What it does:**
- When data exceeds limits, take random sample
- Uses `DataFrame.sample(n=SAMPLE_SIZE, random_state=42)`
- Reproducible sampling (same seed)

**Trade-offs:**
- ✅ Prevents OOM errors
- ✅ Enables caching of large results
- ⚠️ Analysis on sample, not full data
- ⚠️ User needs to know it's sampled

#### 4. Time-to-Live (TTL)
```python
CACHE_TTL_SECONDS=3600  # 1 hour
```

**What it does:**
- Timestamp when cached
- Auto-expire after TTL
- Next access returns "cache expired"

**Prevents:**
- Stale data issues
- Memory leaks from forgotten cache
- Using outdated query results

### Memory Usage Examples

#### Small Query (Safe)
```
SELECT * FROM customers LIMIT 100
Rows: 100
Columns: 10
Size: ~80 KB
✅ Cached in full
```

#### Medium Query (Safe)
```
SELECT * FROM orders WHERE date > '2024-01-01'
Rows: 5,000
Columns: 20
Size: ~8 MB
✅ Cached in full
```

#### Large Query (Sampled)
```
SELECT * FROM transactions
Rows: 1,000,000
Columns: 50
Size: ~400 MB

With AUTO_SAMPLE=true:
✅ Cached 1,000 rows (sample)
Size: ~400 KB
⚠️  User warned: "Large dataset sampled"
```

#### Huge Query (Rejected)
```
SELECT * FROM web_logs
Rows: 100,000,000
Columns: 200
Size: ~150 GB

With AUTO_SAMPLE=false:
❌ Not cached
Message: "Too large (150GB > 100MB)"
Query results still returned, just not cached
```

### Configuration Examples

#### Development (Generous Limits)
```env
ENABLE_DATA_CACHE=true
MAX_CACHE_ROWS=100000       # 100K rows
MAX_CACHE_SIZE_MB=500       # 500MB
CACHE_TTL_SECONDS=7200      # 2 hours
AUTO_SAMPLE_LARGE_RESULTS=true
SAMPLE_SIZE=10000           # 10K sample
```

#### Production (Conservative)
```env
ENABLE_DATA_CACHE=true
MAX_CACHE_ROWS=5000         # 5K rows only
MAX_CACHE_SIZE_MB=50        # 50MB max
CACHE_TTL_SECONDS=1800      # 30 minutes
AUTO_SAMPLE_LARGE_RESULTS=true
SAMPLE_SIZE=500             # Small sample
```

#### High-Memory Server
```env
ENABLE_DATA_CACHE=true
MAX_CACHE_ROWS=1000000      # 1M rows
MAX_CACHE_SIZE_MB=2000      # 2GB
CACHE_TTL_SECONDS=3600
AUTO_SAMPLE_LARGE_RESULTS=false  # Don't sample
SAMPLE_SIZE=0
```

#### Disable Caching
```env
ENABLE_DATA_CACHE=false
# All other settings ignored
```

### How to Monitor Cache

#### Check Cache Info
```python
result = orchestrator.run("query", previous_state=prev)

# Get cache metadata
cache_info = result.metadata.get('cache_info', {})
print(f"Cached: {cache_info['has_cache']}")
print(f"Rows: {cache_info['row_count']}")
print(f"Size: {cache_info['size_mb']} MB")
print(f"Sampled: {cache_info['is_sampled']}")
if cache_info['is_sampled']:
    print(f"Original rows: {cache_info['original_row_count']}")
```

#### Console Logging
```
[SQL Agent] Generated query: SELECT * FROM large_table
[SQL Agent] Retrieved 1000000 results
[SQL Agent] Cache: Cached SAMPLED data: 1000/1000000 rows (0.4MB). Original too large (400.2MB)
[SQL Agent] ⚠️  Large dataset sampled: 1000/1000000 rows cached
```

### Best Practices

#### 1. Add LIMIT to Queries
```sql
-- Bad (can return millions of rows)
SELECT * FROM transactions

-- Good (reasonable result set)
SELECT * FROM transactions LIMIT 10000
```

#### 2. Use Aggregation
```sql
-- Bad (huge cache)
SELECT * FROM orders

-- Good (small summary)
SELECT 
    customer_id, 
    COUNT(*) as order_count,
    SUM(total) as total_spent
FROM orders
GROUP BY customer_id
```

#### 3. Monitor in Streamlit
```python
if 'previous_state' in st.session_state:
    cache_info = st.session_state.previous_state.metadata.get('cache_info')
    if cache_info and cache_info.get('has_cache'):
        st.sidebar.metric("Cached Rows", cache_info['row_count'])
        st.sidebar.metric("Cache Size", f"{cache_info['size_mb']:.1f} MB")
        if cache_info.get('is_sampled'):
            st.sidebar.warning("⚠️ Data is sampled")
```

#### 4. Clear Stale Cache
```python
# Force fresh query (ignore cache)
result = orchestrator.run(
    "SELECT * FROM live_data",
    previous_state=None  # Don't pass previous state
)
```

### Troubleshooting

#### Issue: OOM (Out of Memory) Error
**Symptoms:** App crashes, memory usage spikes
**Cause:** Limits set too high
**Solution:**
```env
MAX_CACHE_ROWS=1000      # Reduce
MAX_CACHE_SIZE_MB=20     # Reduce
AUTO_SAMPLE_LARGE_RESULTS=true  # Enable
```

#### Issue: Analysis on Sampled Data
**Symptoms:** User says "results don't match full dataset"
**Cause:** Auto-sampling active
**Solution:**
1. Check cache_info['is_sampled']
2. Inform user it's a sample
3. Re-run with LIMIT or aggregation

#### Issue: Cache Expires Too Fast
**Symptoms:** Follow-up queries re-execute SQL
**Cause:** TTL too short
**Solution:**
```env
CACHE_TTL_SECONDS=7200  # Increase to 2 hours
# Or set to 0 for no expiration
```

#### Issue: Stale Data
**Symptoms:** Results don't reflect recent DB changes
**Cause:** Cache not expiring
**Solution:**
```env
CACHE_TTL_SECONDS=600  # Expire after 10 minutes
# Or force refresh by not passing previous_state
```

### Advanced: Memory Profiling

#### Check Memory Usage
```python
import psutil
import os

process = psutil.Process(os.getpid())
mem_before = process.memory_info().rss / 1024 / 1024  # MB

result = orchestrator.run("large query")

mem_after = process.memory_info().rss / 1024 / 1024  # MB
print(f"Memory increased: {mem_after - mem_before:.1f} MB")
```

#### Log Cache Statistics
```python
cache_manager = sql_agent.cache_manager
print(f"Cache memory: {cache_manager.get_memory_usage_mb():.1f} MB")
cache_info = cache_manager.get_cache_info()
print(json.dumps(cache_info, indent=2))
```

### Comparison with Alternatives

#### Option 1: No Cache (Current Default for Large Data)
```
Pros: No memory issues, always fresh
Cons: Slow, expensive DB queries repeated
```

#### Option 2: In-Memory Cache (Our Implementation)
```
Pros: Fast, no disk I/O
Cons: Lost on restart, memory limited
```

#### Option 3: Redis Cache (Future Enhancement)
```
Pros: Persistent, shared across instances
Cons: Requires Redis, network latency
```

#### Option 4: Disk Cache (Future Enhancement)
```
Pros: Large capacity, persistent
Cons: Slow I/O, disk space
```

### Future Enhancements

1. **Redis Backend**
   - Persistent cache across restarts
   - Shared cache across multiple users
   - Distributed cache for scaled deployments

2. **Smart Invalidation**
   - Detect when tables are modified
   - Auto-invalidate affected caches
   - Query fingerprinting

3. **Compression**
   - Compress DataFrames in cache
   - Save more data in same memory
   - Trade CPU for memory

4. **Partial Results**
   - Cache aggregations separately
   - Cache query plan metadata
   - Incremental query optimization
