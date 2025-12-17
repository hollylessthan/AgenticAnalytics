"""
Test script for cache safety mechanisms.

Tests the DataCacheManager with various dataset sizes to verify:
1. Small datasets are cached fully
2. Large datasets trigger sampling
3. Huge datasets are rejected if sampling disabled
4. TTL expiration works correctly
5. Memory calculations are accurate
"""

import sys
import os
import time
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import Config
from src.utils.cache_manager import DataCacheManager


def create_test_dataframe(rows: int, cols: int = 10) -> pd.DataFrame:
    """Create a test DataFrame with specified dimensions."""
    data = {
        f'col_{i}': np.random.randn(rows) for i in range(cols)
    }
    return pd.DataFrame(data)


def test_small_dataset():
    """Test 1: Small dataset should cache fully."""
    print("\n" + "="*60)
    print("TEST 1: Small Dataset (100 rows)")
    print("="*60)
    
    config = Config()
    cache_mgr = DataCacheManager(config)
    
    # Create small DataFrame
    df = create_test_dataframe(100, 10)
    print(f"Created DataFrame: {len(df)} rows, {len(df.columns)} columns")
    
    # Check if should cache
    should_cache, reason = cache_mgr.should_cache(df)
    print(f"Should cache: {should_cache}")
    print(f"Reason: {reason}")
    
    # Cache the data
    cached_data, msg = cache_mgr.cache_data(df, "SELECT * FROM small_table LIMIT 100")
    print(f"Cache result: {msg}")
    
    # Get cache info
    info = cache_mgr.get_cache_info()
    print(f"\nCache Info:")
    print(f"  Has cache: {info['has_cache']}")
    print(f"  Row count: {info['row_count']}")
    print(f"  Size: {info['size_mb']:.2f} MB")
    print(f"  Is sampled: {info['is_sampled']}")
    
    # Verify
    assert cached_data is not None, "Small dataset should be cached"
    assert len(cached_data) == 100, "All rows should be cached"
    assert not info['is_sampled'], "Should not be sampled"
    print("\n✅ TEST 1 PASSED: Small dataset cached fully")


def test_medium_dataset():
    """Test 2: Medium dataset within limits should cache fully."""
    print("\n" + "="*60)
    print("TEST 2: Medium Dataset (5,000 rows)")
    print("="*60)
    
    config = Config()
    cache_mgr = DataCacheManager(config)
    
    # Create medium DataFrame
    df = create_test_dataframe(5000, 20)
    print(f"Created DataFrame: {len(df)} rows, {len(df.columns)} columns")
    
    # Check if should cache
    should_cache, reason = cache_mgr.should_cache(df)
    print(f"Should cache: {should_cache}")
    print(f"Reason: {reason}")
    
    # Cache the data
    cached_data, msg = cache_mgr.cache_data(df, "SELECT * FROM medium_table")
    print(f"Cache result: {msg}")
    
    # Get cache info
    info = cache_mgr.get_cache_info()
    print(f"\nCache Info:")
    print(f"  Has cache: {info['has_cache']}")
    print(f"  Row count: {info['row_count']}")
    print(f"  Size: {info['size_mb']:.2f} MB")
    print(f"  Is sampled: {info['is_sampled']}")
    
    # Verify
    assert cached_data is not None, "Medium dataset should be cached"
    assert len(cached_data) == 5000, "All rows should be cached"
    assert not info['is_sampled'], "Should not be sampled"
    print("\n✅ TEST 2 PASSED: Medium dataset cached fully")


def test_large_dataset_with_sampling():
    """Test 3: Large dataset should be sampled."""
    print("\n" + "="*60)
    print("TEST 3: Large Dataset (50,000 rows) with Auto-Sampling")
    print("="*60)
    
    config = Config()
    config.auto_sample_large_results = True
    config.sample_size = 1000
    cache_mgr = DataCacheManager(config)
    
    # Create large DataFrame
    df = create_test_dataframe(50000, 50)
    print(f"Created DataFrame: {len(df)} rows, {len(df.columns)} columns")
    
    # Check if should cache
    should_cache, reason = cache_mgr.should_cache(df)
    print(f"Should cache: {should_cache}")
    print(f"Reason: {reason}")
    
    # Cache the data
    cached_data, msg = cache_mgr.cache_data(df, "SELECT * FROM large_table")
    print(f"Cache result: {msg}")
    
    # Get cache info
    info = cache_mgr.get_cache_info()
    print(f"\nCache Info:")
    print(f"  Has cache: {info['has_cache']}")
    print(f"  Row count: {info['row_count']}")
    print(f"  Original row count: {info.get('original_row_count', 'N/A')}")
    print(f"  Size: {info['size_mb']:.2f} MB")
    print(f"  Is sampled: {info['is_sampled']}")
    
    # Verify
    assert cached_data is not None, "Large dataset should be sampled and cached"
    assert len(cached_data) == 1000, f"Should cache {config.sample_size} rows, got {len(cached_data)}"
    assert info['is_sampled'], "Should be marked as sampled"
    assert info['original_row_count'] == 50000, "Should track original row count"
    print("\n✅ TEST 3 PASSED: Large dataset sampled to 1000 rows")


def test_large_dataset_without_sampling():
    """Test 4: Large dataset without sampling should be rejected."""
    print("\n" + "="*60)
    print("TEST 4: Large Dataset (50,000 rows) WITHOUT Auto-Sampling")
    print("="*60)
    
    config = Config()
    config.auto_sample_large_results = False
    cache_mgr = DataCacheManager(config)
    
    # Create large DataFrame
    df = create_test_dataframe(50000, 50)
    print(f"Created DataFrame: {len(df)} rows, {len(df.columns)} columns")
    
    # Check if should cache
    should_cache, reason = cache_mgr.should_cache(df)
    print(f"Should cache: {should_cache}")
    print(f"Reason: {reason}")
    
    # Cache the data
    cached_data, msg = cache_mgr.cache_data(df, "SELECT * FROM large_table")
    print(f"Cache result: {msg}")
    
    # Get cache info
    info = cache_mgr.get_cache_info()
    print(f"\nCache Info:")
    print(f"  Has cache: {info['has_cache']}")
    
    # Verify
    assert cached_data is None, "Large dataset should NOT be cached without sampling"
    assert not info['has_cache'], "Should have no cache"
    print("\n✅ TEST 4 PASSED: Large dataset rejected without sampling")


def test_ttl_expiration():
    """Test 5: TTL expiration should clear cache."""
    print("\n" + "="*60)
    print("TEST 5: TTL Expiration (2 second timeout)")
    print("="*60)
    
    config = Config()
    config.cache_ttl_seconds = 2  # 2 second TTL for testing
    cache_mgr = DataCacheManager(config)
    
    # Create and cache data
    df = create_test_dataframe(100, 10)
    cached_data, msg = cache_mgr.cache_data(df, "SELECT * FROM test")
    print(f"Cached data: {msg}")
    
    # Verify cache exists
    info = cache_mgr.get_cache_info()
    print(f"Initial cache: {info['has_cache']}")
    print(f"TTL remaining: {info['ttl_remaining']:.1f} seconds")
    assert info['has_cache'], "Cache should exist initially"
    
    # Wait for expiration
    print("\nWaiting 3 seconds for cache to expire...")
    time.sleep(3)
    
    # Check if expired
    retrieved_data = cache_mgr.get_cached_data()
    info = cache_mgr.get_cache_info()
    print(f"After expiration:")
    print(f"  Has cache: {info['has_cache']}")
    print(f"  Retrieved data: {retrieved_data is not None}")
    
    # Verify
    assert retrieved_data is None, "Cache should be expired and return None"
    assert not info['has_cache'], "Cache info should show no cache"
    print("\n✅ TEST 5 PASSED: Cache expired after TTL")


def test_memory_calculation():
    """Test 6: Memory size calculation accuracy."""
    print("\n" + "="*60)
    print("TEST 6: Memory Size Calculation")
    print("="*60)
    
    config = Config()
    cache_mgr = DataCacheManager(config)
    
    # Test different DataFrame sizes
    test_cases = [
        (100, 10, "Small"),
        (1000, 20, "Medium"),
        (10000, 50, "Large"),
    ]
    
    for rows, cols, label in test_cases:
        df = create_test_dataframe(rows, cols)
        size_mb = cache_mgr._calculate_size_mb(df)
        pandas_size_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        print(f"\n{label} DataFrame ({rows} rows × {cols} cols):")
        print(f"  Cache manager: {size_mb:.3f} MB")
        print(f"  Pandas direct:  {pandas_size_mb:.3f} MB")
        print(f"  Match: {abs(size_mb - pandas_size_mb) < 0.001}")
        
        # Verify calculation matches pandas
        assert abs(size_mb - pandas_size_mb) < 0.001, "Size calculation should match pandas"
    
    print("\n✅ TEST 6 PASSED: Memory calculations accurate")


def test_cache_info_accuracy():
    """Test 7: Cache info metadata accuracy."""
    print("\n" + "="*60)
    print("TEST 7: Cache Info Metadata Accuracy")
    print("="*60)
    
    config = Config()
    config.auto_sample_large_results = True
    config.sample_size = 500
    config.max_cache_rows = 5000  # Lower limit to trigger sampling
    cache_mgr = DataCacheManager(config)
    
    # Create and cache large dataset (will be sampled)
    df = create_test_dataframe(10000, 30)
    sql_query = "SELECT * FROM test WHERE date > '2024-01-01'"
    
    cached_data, msg = cache_mgr.cache_data(df, sql_query)
    info = cache_mgr.get_cache_info()
    
    print(f"Cached: {msg}")
    print(f"\nCache Info:")
    print(f"  has_cache: {info['has_cache']}")
    print(f"  row_count: {info['row_count']}")
    print(f"  original_row_count: {info['original_row_count']}")
    print(f"  size_mb: {info['size_mb']:.3f}")
    print(f"  is_sampled: {info['is_sampled']}")
    print(f"  sql_query: {info['sql_query']}")
    print(f"  age: {info['age']:.2f} seconds")
    print(f"  ttl_remaining: {info['ttl_remaining']:.2f} seconds")
    
    # Verify metadata
    assert info['has_cache'] == True
    assert info['row_count'] == 500, f"Expected 500 rows, got {info['row_count']}"
    assert info['original_row_count'] == 10000
    assert info['is_sampled'] == True
    assert info['sql_query'] == sql_query
    assert info['age'] < 1.0, "Age should be less than 1 second"
    assert info['ttl_remaining'] > 3500, "TTL should be close to 3600"
    
    print("\n✅ TEST 7 PASSED: Cache info metadata accurate")


def test_clear_cache():
    """Test 8: Cache clearing."""
    print("\n" + "="*60)
    print("TEST 8: Cache Clearing")
    print("="*60)
    
    config = Config()
    cache_mgr = DataCacheManager(config)
    
    # Create and cache data
    df = create_test_dataframe(100, 10)
    cached_data, msg = cache_mgr.cache_data(df, "SELECT * FROM test")
    
    # Verify cache exists
    info = cache_mgr.get_cache_info()
    print(f"Before clear: has_cache = {info['has_cache']}")
    assert info['has_cache'], "Cache should exist"
    
    # Clear cache
    cache_mgr.clear_cache()
    
    # Verify cache cleared
    info = cache_mgr.get_cache_info()
    print(f"After clear: has_cache = {info['has_cache']}")
    assert not info['has_cache'], "Cache should be cleared"
    
    # Verify retrieval returns None
    retrieved = cache_mgr.get_cached_data()
    assert retrieved is None, "Retrieved data should be None after clear"
    
    print("\n✅ TEST 8 PASSED: Cache cleared successfully")


def run_all_tests():
    """Run all cache safety tests."""
    print("\n" + "="*60)
    print("CACHE SAFETY TEST SUITE")
    print("="*60)
    
    tests = [
        ("Small Dataset", test_small_dataset),
        ("Medium Dataset", test_medium_dataset),
        ("Large Dataset with Sampling", test_large_dataset_with_sampling),
        ("Large Dataset without Sampling", test_large_dataset_without_sampling),
        ("TTL Expiration", test_ttl_expiration),
        ("Memory Calculation", test_memory_calculation),
        ("Cache Info Accuracy", test_cache_info_accuracy),
        ("Cache Clearing", test_clear_cache),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {test_name}")
            print(f"   Error: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"\n❌ TEST ERROR: {test_name}")
            print(f"   Error: {str(e)}")
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
