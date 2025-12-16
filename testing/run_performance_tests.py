#!/usr/bin/env python3
"""
Performance testing script for Agentic Analytics with TPC-DS data
Tests SQL generation, RAG retrieval, analysis, and visualization capabilities
"""

import sys
import os
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.agents.orchestrator import AgentOrchestrator
from src.utils.database_factory import get_database_engine
from src.rag.rag_system import RAGSystem


# Test queries organized by complexity
TEST_QUERIES = {
    "basic": [
        {
            "question": "What are the total sales in the database?",
            "expected_tables": ["store_sales"],
            "complexity": "simple"
        },
        {
            "question": "How many customers do we have?",
            "expected_tables": ["customer"],
            "complexity": "simple"
        },
        {
            "question": "List all product categories",
            "expected_tables": ["item"],
            "complexity": "simple"
        }
    ],
    "intermediate": [
        {
            "question": "What are the total sales by year?",
            "expected_tables": ["store_sales", "date_dim"],
            "complexity": "aggregation"
        },
        {
            "question": "Show the top 10 best-selling products",
            "expected_tables": ["store_sales", "item"],
            "complexity": "join_aggregation"
        },
        {
            "question": "What are sales by product category?",
            "expected_tables": ["store_sales", "item"],
            "complexity": "join_aggregation"
        },
        {
            "question": "Which stores have the highest revenue?",
            "expected_tables": ["store_sales", "store"],
            "complexity": "join_aggregation"
        }
    ],
    "advanced": [
        {
            "question": "Calculate year-over-year sales growth by quarter",
            "expected_tables": ["store_sales", "date_dim"],
            "complexity": "window_function"
        },
        {
            "question": "What products have the highest return rates and why?",
            "expected_tables": ["store_sales", "store_returns", "item", "reason"],
            "complexity": "multi_join"
        },
        {
            "question": "Show monthly sales trends with 3-month moving average",
            "expected_tables": ["store_sales", "date_dim"],
            "complexity": "window_function"
        },
        {
            "question": "Identify customers with declining purchase frequency",
            "expected_tables": ["customer", "store_sales", "date_dim"],
            "complexity": "complex_analysis"
        }
    ],
    "visualization": [
        {
            "question": "Create a bar chart of sales by year",
            "expected_tables": ["store_sales", "date_dim"],
            "complexity": "visualization",
            "chart_type": "bar"
        },
        {
            "question": "Show a line graph of daily sales trends for the last quarter",
            "expected_tables": ["store_sales", "date_dim"],
            "complexity": "visualization",
            "chart_type": "line"
        },
        {
            "question": "Create a pie chart of sales by product category",
            "expected_tables": ["store_sales", "item"],
            "complexity": "visualization",
            "chart_type": "pie"
        }
    ],
    "multi_channel": [
        {
            "question": "Compare sales across all channels (store, catalog, web)",
            "expected_tables": ["store_sales", "catalog_sales", "web_sales", "date_dim"],
            "complexity": "multi_table_union"
        },
        {
            "question": "Which channel has the highest return rate?",
            "expected_tables": ["store_sales", "catalog_sales", "web_sales", "store_returns", "catalog_returns", "web_returns"],
            "complexity": "cross_channel_analysis"
        }
    ]
}


class PerformanceTest:
    def __init__(self, db_path: str, rag_enabled: bool = False, rag_docs_path: str = None):
        """Initialize performance testing"""
        self.db_path = db_path
        self.rag_enabled = rag_enabled
        self.results = []
        
        # Setup configuration
        self.config = Config()
        self.config.DATABASE_TYPE = "duckdb"
        self.config.DATABASE_PATH = db_path
        self.config.RAG_ENABLED = rag_enabled
        
        # Initialize database
        print("📊 Initializing database connection...")
        self.engine = get_database_engine(self.config)
        
        # Initialize RAG if enabled
        self.rag_system = None
        if rag_enabled and rag_docs_path:
            print("🔍 Initializing RAG system...")
            self.rag_system = RAGSystem(self.config)
            # TODO: Load documents from rag_docs_path
        
        # Initialize orchestrator
        print("🤖 Initializing agent orchestrator...")
        self.orchestrator = AgentOrchestrator(self.config, self.engine)
    
    def run_query(self, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test query and measure performance"""
        question = query_info["question"]
        print(f"\n{'='*70}")
        print(f"❓ Question: {question}")
        print(f"🎯 Complexity: {query_info['complexity']}")
        print(f"{'='*70}")
        
        result = {
            "question": question,
            "complexity": query_info["complexity"],
            "expected_tables": query_info.get("expected_tables", []),
            "timestamp": datetime.now().isoformat()
        }
        
        # Measure total time
        start_time = time.time()
        
        try:
            # Run orchestrator
            response = self.orchestrator.run(question)
            
            total_time = time.time() - start_time
            
            # Extract metrics
            result["success"] = True
            result["total_time"] = round(total_time, 2)
            result["sql_generated"] = response.get("sql_query", "")
            result["data_retrieved"] = response.get("data") is not None
            result["analysis_provided"] = bool(response.get("analysis", ""))
            result["visualization_created"] = response.get("visualization_path") is not None
            
            # Print results
            print(f"\n✅ SUCCESS ({total_time:.2f}s)")
            if result["sql_generated"]:
                print(f"\n📝 SQL Generated:")
                print(result["sql_generated"])
            if result["analysis_provided"]:
                print(f"\n💡 Analysis:")
                print(response.get("analysis", "")[:200] + "...")
            
        except Exception as e:
            total_time = time.time() - start_time
            result["success"] = False
            result["total_time"] = round(total_time, 2)
            result["error"] = str(e)
            print(f"\n❌ FAILED ({total_time:.2f}s): {e}")
        
        self.results.append(result)
        return result
    
    def run_test_suite(self, test_type: str = "basic"):
        """Run a full test suite"""
        print(f"\n🚀 Running {test_type.upper()} test suite")
        print("="*70)
        
        if test_type not in TEST_QUERIES:
            print(f"❌ Unknown test type: {test_type}")
            print(f"Available types: {', '.join(TEST_QUERIES.keys())}")
            return
        
        queries = TEST_QUERIES[test_type]
        
        for i, query_info in enumerate(queries, 1):
            print(f"\n📍 Test {i}/{len(queries)}")
            self.run_query(query_info)
            time.sleep(1)  # Brief pause between queries
    
    def run_all_tests(self):
        """Run all test suites"""
        for test_type in ["basic", "intermediate", "advanced"]:
            self.run_test_suite(test_type)
    
    def print_summary(self):
        """Print test summary with statistics"""
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        if not self.results:
            print("No tests run")
            return
        
        total_tests = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total_tests - successful
        
        total_time = sum(r["total_time"] for r in self.results)
        avg_time = total_time / total_tests
        
        print(f"\n📈 Overall Results:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Successful: {successful} ({100*successful/total_tests:.1f}%)")
        print(f"  Failed: {failed} ({100*failed/total_tests:.1f}%)")
        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Average Time: {avg_time:.2f}s")
        
        # Performance by complexity
        print(f"\n⏱️  Performance by Complexity:")
        complexity_times = {}
        for result in self.results:
            if result["success"]:
                complexity = result["complexity"]
                if complexity not in complexity_times:
                    complexity_times[complexity] = []
                complexity_times[complexity].append(result["total_time"])
        
        for complexity, times in sorted(complexity_times.items()):
            avg = sum(times) / len(times)
            print(f"  {complexity:20s}: {avg:6.2f}s avg ({len(times)} queries)")
        
        # Detailed failures
        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['question']}")
                    print(f"    Error: {result.get('error', 'Unknown')}")
        
        # Feature coverage
        print(f"\n🎯 Feature Coverage:")
        sql_generated = sum(1 for r in self.results if r.get("sql_generated"))
        data_retrieved = sum(1 for r in self.results if r.get("data_retrieved"))
        analysis_provided = sum(1 for r in self.results if r.get("analysis_provided"))
        viz_created = sum(1 for r in self.results if r.get("visualization_created"))
        
        print(f"  SQL Generation: {sql_generated}/{total_tests} ({100*sql_generated/total_tests:.1f}%)")
        print(f"  Data Retrieval: {data_retrieved}/{total_tests} ({100*data_retrieved/total_tests:.1f}%)")
        print(f"  Analysis: {analysis_provided}/{total_tests} ({100*analysis_provided/total_tests:.1f}%)")
        print(f"  Visualization: {viz_created}/{total_tests} ({100*viz_created/total_tests:.1f}%)")
    
    def save_results(self, output_path: str):
        """Save detailed results to JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        summary = {
            "test_date": datetime.now().isoformat(),
            "database": self.db_path,
            "rag_enabled": self.rag_enabled,
            "total_tests": len(self.results),
            "successful": sum(1 for r in self.results if r["success"]),
            "results": self.results
        }
        
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Run performance tests on Agentic Analytics")
    parser.add_argument("--db-path", type=str, default="tpcds_100gb.duckdb", help="DuckDB database path")
    parser.add_argument("--test", type=str, default="basic", help="Test suite: basic, intermediate, advanced, all")
    parser.add_argument("--rag-enabled", action="store_true", help="Enable RAG system")
    parser.add_argument("--rag-docs", type=str, default="rag_documents", help="RAG documents directory")
    parser.add_argument("--output", type=str, default="test_results.json", help="Output file for results")
    args = parser.parse_args()
    
    print("🧪 Agentic Analytics Performance Testing")
    print("="*70)
    print(f"Database: {args.db_path}")
    print(f"Test Suite: {args.test}")
    print(f"RAG Enabled: {args.rag_enabled}")
    print("="*70)
    
    # Check database exists
    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"\n❌ Error: Database not found: {db_path}")
        print("Run setup_tpcds_duckdb.py first!")
        sys.exit(1)
    
    # Initialize tester
    tester = PerformanceTest(
        db_path=str(db_path),
        rag_enabled=args.rag_enabled,
        rag_docs_path=args.rag_docs if args.rag_enabled else None
    )
    
    # Run tests
    if args.test == "all":
        tester.run_all_tests()
    else:
        tester.run_test_suite(args.test)
    
    # Print summary
    tester.print_summary()
    
    # Save results
    tester.save_results(args.output)
    
    print("\n✅ Testing complete!")


if __name__ == "__main__":
    main()
