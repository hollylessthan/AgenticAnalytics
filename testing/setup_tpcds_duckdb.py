#!/usr/bin/env python3
"""
Load TPC-DS data into DuckDB
Handles large datasets efficiently with batching and progress tracking
"""

import duckdb
import os
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, List

# TPC-DS column type definitions (proper types instead of all VARCHAR)
TPCDS_COLUMN_TYPES = {
    # Numeric columns
    "quantity": "INTEGER",
    "quantity_on_hand": "INTEGER", 
    "inv_quantity_on_hand": "INTEGER",
    "ss_quantity": "INTEGER",
    "cs_quantity": "INTEGER",
    "ws_quantity": "INTEGER",
    "sr_return_quantity": "INTEGER",
    "cr_return_quantity": "INTEGER",
    "wr_return_quantity": "INTEGER",
    "p_response_target": "INTEGER",
    "cc_employees": "INTEGER",
    "s_number_employees": "INTEGER",
    "hd_dep_count": "INTEGER",
    "hd_vehicle_count": "INTEGER",
    "cd_dep_count": "INTEGER",
    "cd_dep_employed_count": "INTEGER",
    "cd_dep_college_count": "INTEGER",
    "d_dom": "INTEGER",
    "d_moy": "INTEGER",
    "d_qoy": "INTEGER",
    "d_year": "INTEGER",
    "d_dow": "INTEGER",
    "d_month_seq": "INTEGER",
    "d_week_seq": "INTEGER",
    "d_quarter_seq": "INTEGER",
    "d_fy_year": "INTEGER",
    "d_fy_quarter_seq": "INTEGER",
    "d_fy_week_seq": "INTEGER",
    "t_hour": "INTEGER",
    "t_minute": "INTEGER",
    "t_second": "INTEGER",
    
    # Price/Cost columns (DECIMAL for financial data)
    "wholesale_cost": "DECIMAL(10,2)",
    "list_price": "DECIMAL(10,2)",
    "sales_price": "DECIMAL(10,2)",
    "ext_discount_amt": "DECIMAL(10,2)",
    "ext_sales_price": "DECIMAL(10,2)",
    "ext_wholesale_cost": "DECIMAL(10,2)",
    "ext_list_price": "DECIMAL(10,2)",
    "ext_tax": "DECIMAL(10,2)",
    "coupon_amt": "DECIMAL(10,2)",
    "ext_ship_cost": "DECIMAL(10,2)",
    "net_paid": "DECIMAL(10,2)",
    "net_paid_inc_tax": "DECIMAL(10,2)",
    "net_paid_inc_ship": "DECIMAL(10,2)",
    "net_paid_inc_ship_tax": "DECIMAL(10,2)",
    "net_profit": "DECIMAL(10,2)",
    "return_amount": "DECIMAL(10,2)",
    "return_tax": "DECIMAL(10,2)",
    "return_amt_inc_tax": "DECIMAL(10,2)",
    "fee": "DECIMAL(10,2)",
    "return_ship_cost": "DECIMAL(10,2)",
    "refunded_cash": "DECIMAL(10,2)",
    "reversed_charge": "DECIMAL(10,2)",
    "store_credit": "DECIMAL(10,2)",
    "net_loss": "DECIMAL(10,2)",
    "account_credit": "DECIMAL(10,2)",
    "cost": "DECIMAL(10,2)",
    "purchase_estimate": "INTEGER",
    "ib_lower_bound": "INTEGER",
    "ib_upper_bound": "INTEGER",
    "current_price": "DECIMAL(10,2)",
    "tax_percentage": "DECIMAL(10,2)",
    "gmt_offset": "DECIMAL(5,2)",
    "sq_ft": "INTEGER",
    "floor_space": "INTEGER",
    "char_count": "INTEGER",
    "link_count": "INTEGER",
    "image_count": "INTEGER",
    "max_ad_count": "INTEGER",
    
    # Date columns (DATE type)
    "date": "DATE",
    "rec_start_date": "DATE",
    "rec_end_date": "DATE",
    "closed_date_sk": "INTEGER",
    "open_date_sk": "INTEGER",
    "start_date_sk": "INTEGER",
    "end_date_sk": "INTEGER",
    "first_shipto_date_sk": "INTEGER",
    "first_sales_date_sk": "INTEGER",
    "birth_day": "INTEGER",
    "birth_month": "INTEGER",
    "birth_year": "INTEGER",
    "creation_date_sk": "INTEGER",
    "access_date_sk": "INTEGER",
    "returned_date_sk": "INTEGER",
    "returned_time_sk": "INTEGER",
    "ship_date_sk": "INTEGER",
    "sold_date_sk": "INTEGER",
    "sold_time_sk": "INTEGER",
    "ship_mode_sk": "INTEGER",
    "warehouse_sk": "INTEGER",
    
    # Surrogate keys (INTEGER)
    "_sk": "INTEGER",
    
    # Default for anything else: VARCHAR
}

# TPC-DS table definitions with columns
TPCDS_TABLES = {
    "call_center": ["cc_call_center_sk", "cc_call_center_id", "cc_rec_start_date", "cc_rec_end_date", "cc_closed_date_sk", "cc_open_date_sk", "cc_name", "cc_class", "cc_employees", "cc_sq_ft", "cc_hours", "cc_manager", "cc_mkt_id", "cc_mkt_class", "cc_mkt_desc", "cc_market_manager", "cc_division", "cc_division_name", "cc_company", "cc_company_name", "cc_street_number", "cc_street_name", "cc_street_type", "cc_suite_number", "cc_city", "cc_county", "cc_state", "cc_zip", "cc_country", "cc_gmt_offset", "cc_tax_percentage"],
    "catalog_page": ["cp_catalog_page_sk", "cp_catalog_page_id", "cp_start_date_sk", "cp_end_date_sk", "cp_department", "cp_catalog_number", "cp_catalog_page_number", "cp_description", "cp_type"],
    "catalog_returns": ["cr_returned_date_sk", "cr_returned_time_sk", "cr_item_sk", "cr_refunded_customer_sk", "cr_refunded_cdemo_sk", "cr_refunded_hdemo_sk", "cr_refunded_addr_sk", "cr_returning_customer_sk", "cr_returning_cdemo_sk", "cr_returning_hdemo_sk", "cr_returning_addr_sk", "cr_call_center_sk", "cr_catalog_page_sk", "cr_ship_mode_sk", "cr_warehouse_sk", "cr_reason_sk", "cr_order_number", "cr_return_quantity", "cr_return_amount", "cr_return_tax", "cr_return_amt_inc_tax", "cr_fee", "cr_return_ship_cost", "cr_refunded_cash", "cr_reversed_charge", "cr_store_credit", "cr_net_loss"],
    "catalog_sales": ["cs_sold_date_sk", "cs_sold_time_sk", "cs_ship_date_sk", "cs_bill_customer_sk", "cs_bill_cdemo_sk", "cs_bill_hdemo_sk", "cs_bill_addr_sk", "cs_ship_customer_sk", "cs_ship_cdemo_sk", "cs_ship_hdemo_sk", "cs_ship_addr_sk", "cs_call_center_sk", "cs_catalog_page_sk", "cs_ship_mode_sk", "cs_warehouse_sk", "cs_item_sk", "cs_promo_sk", "cs_order_number", "cs_quantity", "cs_wholesale_cost", "cs_list_price", "cs_sales_price", "cs_ext_discount_amt", "cs_ext_sales_price", "cs_ext_wholesale_cost", "cs_ext_list_price", "cs_ext_tax", "cs_coupon_amt", "cs_ext_ship_cost", "cs_net_paid", "cs_net_paid_inc_tax", "cs_net_paid_inc_ship", "cs_net_paid_inc_ship_tax", "cs_net_profit"],
    "customer": ["c_customer_sk", "c_customer_id", "c_current_cdemo_sk", "c_current_hdemo_sk", "c_current_addr_sk", "c_first_shipto_date_sk", "c_first_sales_date_sk", "c_salutation", "c_first_name", "c_last_name", "c_preferred_cust_flag", "c_birth_day", "c_birth_month", "c_birth_year", "c_birth_country", "c_login", "c_email_address", "c_last_review_date_sk"],
    "customer_address": ["ca_address_sk", "ca_address_id", "ca_street_number", "ca_street_name", "ca_street_type", "ca_suite_number", "ca_city", "ca_county", "ca_state", "ca_zip", "ca_country", "ca_gmt_offset", "ca_location_type"],
    "customer_demographics": ["cd_demo_sk", "cd_gender", "cd_marital_status", "cd_education_status", "cd_purchase_estimate", "cd_credit_rating", "cd_dep_count", "cd_dep_employed_count", "cd_dep_college_count"],
    "date_dim": ["d_date_sk", "d_date_id", "d_date", "d_month_seq", "d_week_seq", "d_quarter_seq", "d_year", "d_dow", "d_moy", "d_dom", "d_qoy", "d_fy_year", "d_fy_quarter_seq", "d_fy_week_seq", "d_day_name", "d_quarter_name", "d_holiday", "d_weekend", "d_following_holiday", "d_first_dom", "d_last_dom", "d_same_day_ly", "d_same_day_lq", "d_current_day", "d_current_week", "d_current_month", "d_current_quarter", "d_current_year"],
    "household_demographics": ["hd_demo_sk", "hd_income_band_sk", "hd_buy_potential", "hd_dep_count", "hd_vehicle_count"],
    "income_band": ["ib_income_band_sk", "ib_lower_bound", "ib_upper_bound"],
    "inventory": ["inv_date_sk", "inv_item_sk", "inv_warehouse_sk", "inv_quantity_on_hand"],
    "item": ["i_item_sk", "i_item_id", "i_rec_start_date", "i_rec_end_date", "i_item_desc", "i_current_price", "i_wholesale_cost", "i_brand_id", "i_brand", "i_class_id", "i_class", "i_category_id", "i_category", "i_manufact_id", "i_manufact", "i_size", "i_formulation", "i_color", "i_units", "i_container", "i_manager_id", "i_product_name"],
    "promotion": ["p_promo_sk", "p_promo_id", "p_start_date_sk", "p_end_date_sk", "p_item_sk", "p_cost", "p_response_target", "p_promo_name", "p_channel_dmail", "p_channel_email", "p_channel_catalog", "p_channel_tv", "p_channel_radio", "p_channel_press", "p_channel_event", "p_channel_demo", "p_channel_details", "p_purpose", "p_discount_active"],
    "reason": ["r_reason_sk", "r_reason_id", "r_reason_desc"],
    "ship_mode": ["sm_ship_mode_sk", "sm_ship_mode_id", "sm_type", "sm_code", "sm_carrier", "sm_contract"],
    "store": ["s_store_sk", "s_store_id", "s_rec_start_date", "s_rec_end_date", "s_closed_date_sk", "s_store_name", "s_number_employees", "s_floor_space", "s_hours", "s_manager", "s_market_id", "s_geography_class", "s_market_desc", "s_market_manager", "s_division_id", "s_division_name", "s_company_id", "s_company_name", "s_street_number", "s_street_name", "s_street_type", "s_suite_number", "s_city", "s_county", "s_state", "s_zip", "s_country", "s_gmt_offset", "s_tax_percentage"],
    "store_returns": ["sr_returned_date_sk", "sr_return_time_sk", "sr_item_sk", "sr_customer_sk", "sr_cdemo_sk", "sr_hdemo_sk", "sr_addr_sk", "sr_store_sk", "sr_reason_sk", "sr_ticket_number", "sr_return_quantity", "sr_return_amt", "sr_return_tax", "sr_return_amt_inc_tax", "sr_fee", "sr_return_ship_cost", "sr_refunded_cash", "sr_reversed_charge", "sr_store_credit", "sr_net_loss"],
    "store_sales": ["ss_sold_date_sk", "ss_sold_time_sk", "ss_item_sk", "ss_customer_sk", "ss_cdemo_sk", "ss_hdemo_sk", "ss_addr_sk", "ss_store_sk", "ss_promo_sk", "ss_ticket_number", "ss_quantity", "ss_wholesale_cost", "ss_list_price", "ss_sales_price", "ss_ext_discount_amt", "ss_ext_sales_price", "ss_ext_wholesale_cost", "ss_ext_list_price", "ss_ext_tax", "ss_coupon_amt", "ss_net_paid", "ss_net_paid_inc_tax", "ss_net_profit"],
    "time_dim": ["t_time_sk", "t_time_id", "t_time", "t_hour", "t_minute", "t_second", "t_am_pm", "t_shift", "t_sub_shift", "t_meal_time"],
    "warehouse": ["w_warehouse_sk", "w_warehouse_id", "w_warehouse_name", "w_warehouse_sq_ft", "w_street_number", "w_street_name", "w_street_type", "w_suite_number", "w_city", "w_county", "w_state", "w_zip", "w_country", "w_gmt_offset"],
    "web_page": ["wp_web_page_sk", "wp_web_page_id", "wp_rec_start_date", "wp_rec_end_date", "wp_creation_date_sk", "wp_access_date_sk", "wp_autogen_flag", "wp_customer_sk", "wp_url", "wp_type", "wp_char_count", "wp_link_count", "wp_image_count", "wp_max_ad_count"],
    "web_returns": ["wr_returned_date_sk", "wr_returned_time_sk", "wr_item_sk", "wr_refunded_customer_sk", "wr_refunded_cdemo_sk", "wr_refunded_hdemo_sk", "wr_refunded_addr_sk", "wr_returning_customer_sk", "wr_returning_cdemo_sk", "wr_returning_hdemo_sk", "wr_returning_addr_sk", "wr_web_page_sk", "wr_reason_sk", "wr_order_number", "wr_return_quantity", "wr_return_amt", "wr_return_tax", "wr_return_amt_inc_tax", "wr_fee", "wr_return_ship_cost", "wr_refunded_cash", "wr_reversed_charge", "wr_account_credit", "wr_net_loss"],
    "web_sales": ["ws_sold_date_sk", "ws_sold_time_sk", "ws_ship_date_sk", "ws_item_sk", "ws_bill_customer_sk", "ws_bill_cdemo_sk", "ws_bill_hdemo_sk", "ws_bill_addr_sk", "ws_ship_customer_sk", "ws_ship_cdemo_sk", "ws_ship_hdemo_sk", "ws_ship_addr_sk", "ws_web_page_sk", "ws_web_site_sk", "ws_ship_mode_sk", "ws_warehouse_sk", "ws_promo_sk", "ws_order_number", "ws_quantity", "ws_wholesale_cost", "ws_list_price", "ws_sales_price", "ws_ext_discount_amt", "ws_ext_sales_price", "ws_ext_wholesale_cost", "ws_ext_list_price", "ws_ext_tax", "ws_coupon_amt", "ws_ext_ship_cost", "ws_net_paid", "ws_net_paid_inc_tax", "ws_net_paid_inc_ship", "ws_net_paid_inc_ship_tax", "ws_net_profit"],
    "web_site": ["web_site_sk", "web_site_id", "web_rec_start_date", "web_rec_end_date", "web_name", "web_open_date_sk", "web_close_date_sk", "web_class", "web_manager", "web_mkt_id", "web_mkt_class", "web_mkt_desc", "web_market_manager", "web_company_id", "web_company_name", "web_street_number", "web_street_name", "web_street_type", "web_suite_number", "web_city", "web_county", "web_state", "web_zip", "web_country", "web_gmt_offset", "web_tax_percentage"],
}


def get_column_type(column_name: str) -> str:
    """Determine the proper DuckDB type for a column based on name"""
    col_lower = column_name.lower()
    
    # NOTE: Load all columns as VARCHAR initially
    # We'll cast date columns in a second pass after loading
    # This avoids DuckDB's CSV date parsing issues
    return "VARCHAR"


def get_final_column_type(column_name: str) -> str:
    """Get the final type for a column (for casting after load)"""
    col_lower = column_name.lower()
    
    # Check exact matches first
    if col_lower in TPCDS_COLUMN_TYPES:
        return TPCDS_COLUMN_TYPES[col_lower]
    
    # Check partial matches
    for pattern, dtype in TPCDS_COLUMN_TYPES.items():
        if pattern in col_lower:
            return dtype
    
    # Default to VARCHAR
    return "VARCHAR"


def cast_table_columns(conn: duckdb.DuckDBPyConnection, table_name: str) -> None:
    """Cast columns to their proper types after loading as VARCHAR"""
    columns = TPCDS_TABLES[table_name]
    
    for col in columns:
        final_type = get_final_column_type(col)
        
        # Only cast if type is not VARCHAR (otherwise already correct)
        if final_type != "VARCHAR":
            try:
                if final_type == "DATE":
                    # Cast string to DATE
                    conn.execute(f"ALTER TABLE {table_name} ALTER COLUMN {col} SET DATA TYPE DATE")
                elif final_type.startswith("DECIMAL"):
                    # Cast string to DECIMAL
                    conn.execute(f"ALTER TABLE {table_name} ALTER COLUMN {col} SET DATA TYPE {final_type}")
                elif final_type == "INTEGER":
                    # Cast string to INTEGER
                    conn.execute(f"ALTER TABLE {table_name} ALTER COLUMN {col} SET DATA TYPE INTEGER")
            except Exception as e:
                # Skip if casting fails for this column
                pass


def load_table(conn: duckdb.DuckDBPyConnection, table_name: str, data_dir: Path) -> Dict:
    """Load a single table from TPC-DS data files"""
    data_file = data_dir / f"{table_name}.dat"
    
    if not data_file.exists():
        return {"status": "skipped", "reason": "file not found"}
    
    print(f"  Loading {table_name}...", end=" ", flush=True)
    start_time = time.time()
    
    try:
        # Create column list with proper types
        columns = TPCDS_TABLES[table_name]
        column_defs = ", ".join([f"'{col}': '{get_column_type(col)}'" for col in columns])
        
        # Read CSV with DuckDB (very efficient)
        # Note: TPC-DS files use | as delimiter and have trailing delimiter
        query = f"""
        CREATE TABLE {table_name} AS 
        SELECT * FROM read_csv(
            '{data_file}',
            delim='|',
            header=false,
            columns={{{column_defs}}},
            nullstr='',
            ignore_errors=true
        )
        """
        
        conn.execute(query)
        
        # Get row count
        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        
        duration = time.time() - start_time
        print(f"✅ {row_count:,} rows in {duration:.1f}s")
        
        return {
            "status": "success",
            "rows": row_count,
            "duration": duration
        }
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return {"status": "failed", "error": str(e)}


def create_indexes(conn: duckdb.DuckDBPyConnection):
    """Create indexes on key columns for better query performance"""
    print("\n📊 Creating indexes...")
    
    indexes = [
        ("store_sales", "ss_sold_date_sk"),
        ("store_sales", "ss_customer_sk"),
        ("store_sales", "ss_item_sk"),
        ("catalog_sales", "cs_sold_date_sk"),
        ("catalog_sales", "cs_bill_customer_sk"),
        ("web_sales", "ws_sold_date_sk"),
        ("web_sales", "ws_bill_customer_sk"),
        ("customer", "c_customer_sk"),
        ("item", "i_item_sk"),
        ("date_dim", "d_date_sk"),
    ]
    
    for table, column in indexes:
        try:
            # Check if table exists
            result = conn.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table}'").fetchone()
            if result[0] > 0:
                print(f"  Creating index on {table}.{column}...", end=" ", flush=True)
                # DuckDB creates indexes automatically, but we can hint with ORDER BY
                conn.execute(f"CREATE INDEX idx_{table}_{column} ON {table}({column})")
                print("✅")
        except Exception as e:
            print(f"⚠️  Skipped: {e}")


def analyze_tables(conn: duckdb.DuckDBPyConnection):
    """Run ANALYZE to update statistics"""
    print("\n📈 Analyzing tables for query optimization...")
    conn.execute("ANALYZE")
    print("✅ Statistics updated")


def validate_data(conn: duckdb.DuckDBPyConnection):
    """Basic data validation"""
    print("\n🔍 Validating data...")
    
    # Check for fact tables
    fact_tables = ["store_sales", "catalog_sales", "web_sales"]
    for table in fact_tables:
        try:
            result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            if result[0] > 0:
                print(f"  ✅ {table}: {result[0]:,} rows")
            else:
                print(f"  ⚠️  {table}: empty")
        except:
            print(f"  ❌ {table}: not found")
    
    # Check date range
    try:
        result = conn.execute("""
            SELECT MIN(d_date), MAX(d_date) 
            FROM date_dim
        """).fetchone()
        print(f"  📅 Date range: {result[0]} to {result[1]}")
    except:
        print("  ⚠️  Could not determine date range")


def print_summary(conn: duckdb.DuckDBPyConnection, db_path: Path):
    """Print database summary"""
    print("\n" + "="*60)
    print("📊 DATABASE SUMMARY")
    print("="*60)
    
    # Database size
    db_size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"Database file: {db_path}")
    print(f"Database size: {db_size_mb:.1f} MB")
    
    # Table statistics
    print("\nTable Statistics:")
    tables = conn.execute("SHOW TABLES").fetchall()
    
    total_rows = 0
    for (table_name,) in sorted(tables):
        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        total_rows += row_count
        print(f"  {table_name:25s} {row_count:>15,} rows")
    
    print(f"\n  {'TOTAL':25s} {total_rows:>15,} rows")
    
    # Compression ratio
    data_dir = Path("data/tpcds")
    if data_dir.exists():
        csv_size_mb = sum(f.stat().st_size for f in data_dir.glob("*.dat")) / (1024 * 1024)
        compression_ratio = csv_size_mb / db_size_mb if db_size_mb > 0 else 0
        print(f"\n💾 Storage:")
        print(f"  CSV files: {csv_size_mb:.1f} MB")
        print(f"  DuckDB: {db_size_mb:.1f} MB")
        print(f"  Compression: {compression_ratio:.1f}x")


def main():
    parser = argparse.ArgumentParser(description="Load TPC-DS data into DuckDB")
    parser.add_argument("--scale", type=int, default=1, help="Scale factor (GB)")
    parser.add_argument("--data-dir", type=str, default="data/tpcds", help="TPC-DS data directory")
    parser.add_argument("--db-path", type=str, default=None, help="Output database path")
    args = parser.parse_args()
    
    # Paths
    data_dir = Path(args.data_dir)
    if args.db_path:
        db_path = Path(args.db_path)
    else:
        db_path = Path(f"tpcds_{args.scale}gb.duckdb")
    
    print("🦆 TPC-DS DuckDB Setup")
    print("="*60)
    print(f"Scale Factor: {args.scale}GB")
    print(f"Data Directory: {data_dir}")
    print(f"Database: {db_path}")
    print("="*60)
    
    # Check if data directory exists
    if not data_dir.exists():
        print(f"\n❌ Error: Data directory not found: {data_dir}")
        print("Run ./generate_tpcds_data.sh first!")
        sys.exit(1)
    
    # Delete existing database if it exists
    if db_path.exists():
        print(f"\n⚠️  Database already exists: {db_path}")
        response = input("Delete and recreate? (y/N): ")
        if response.lower() == 'y':
            db_path.unlink()
            print("🗑️  Deleted existing database")
        else:
            print("✅ Using existing database")
            return
    
    # Create database connection
    print(f"\n🔧 Creating database: {db_path}")
    conn = duckdb.connect(str(db_path))
    
    # Set DuckDB configuration for large datasets
    conn.execute("SET memory_limit='8GB'")
    conn.execute("SET threads TO 4")
    
    # Load all tables
    print("\n📥 Loading tables...")
    results = {}
    
    for table_name in sorted(TPCDS_TABLES.keys()):
        results[table_name] = load_table(conn, table_name, data_dir)
        # Cast columns to proper types after loading as VARCHAR
        cast_table_columns(conn, table_name)
    
    # Create indexes
    create_indexes(conn)
    
    # Analyze tables
    analyze_tables(conn)
    
    # Validate
    validate_data(conn)
    
    # Print summary
    print_summary(conn, db_path)
    
    # Close connection
    conn.close()
    
    print("\n" + "="*60)
    print("✅ Setup complete!")
    print("="*60)
    print("\n🎯 Next steps:")
    print("   1. Generate RAG documents: python generate_rag_documents.py")
    print("   2. Run tests: python run_performance_tests.py")
    print(f"   3. Connect: duckdb {db_path}")
    print("\n💡 Example queries:")
    print(f"   duckdb {db_path} \"SELECT COUNT(*) FROM store_sales\"")
    print(f"   duckdb {db_path} \"SELECT d_year, SUM(ss_sales_price) FROM store_sales JOIN date_dim ON ss_sold_date_sk = d_date_sk GROUP BY d_year\"")


if __name__ == "__main__":
    main()
