#!/usr/bin/env python3
"""
Generate comprehensive RAG documents from TPC-DS schema
Creates markdown documentation for schema understanding and query generation
"""

import duckdb
import json
from pathlib import Path
from typing import Dict, List, Any
import argparse


# TPC-DS business context and descriptions
TABLE_DESCRIPTIONS = {
    "store_sales": {
        "description": "Primary fact table containing all sales transactions at physical stores",
        "business_context": "Records every item sold at stores, including prices, discounts, and associated dimensions",
        "key_metrics": ["sales revenue", "quantity sold", "profit margins", "discount amounts"],
        "common_queries": ["daily sales", "top products", "sales by store", "revenue trends"]
    },
    "store_returns": {
        "description": "Returns of items previously purchased at stores",
        "business_context": "Tracks customer returns for analysis of product quality and customer satisfaction",
        "key_metrics": ["return rate", "return amount", "net loss"],
        "common_queries": ["return rates by product", "return reasons", "refund analysis"]
    },
    "catalog_sales": {
        "description": "Sales made through catalog/mail orders",
        "business_context": "Alternative sales channel for customers who order by catalog",
        "key_metrics": ["catalog revenue", "shipping costs", "order volumes"],
        "common_queries": ["catalog vs store sales", "shipping analysis", "channel comparison"]
    },
    "catalog_returns": {
        "description": "Returns of catalog/mail order purchases",
        "business_context": "Returns for catalog channel, often with different return patterns than stores",
        "key_metrics": ["catalog return rate", "shipping cost impact"],
        "common_queries": ["catalog return analysis", "shipping cost recovery"]
    },
    "web_sales": {
        "description": "Online sales made through the website",
        "business_context": "Growing digital sales channel with different customer behavior",
        "key_metrics": ["online revenue", "conversion rates", "digital orders"],
        "common_queries": ["online vs offline sales", "web growth trends", "digital customer behavior"]
    },
    "web_returns": {
        "description": "Returns of items purchased online",
        "business_context": "Online return patterns, typically higher than physical stores",
        "key_metrics": ["online return rate", "reverse logistics cost"],
        "common_queries": ["online return analysis", "digital vs physical return rates"]
    },
    "inventory": {
        "description": "Daily inventory levels at warehouses",
        "business_context": "Track stock levels for supply chain optimization",
        "key_metrics": ["stock levels", "inventory turnover", "stockouts"],
        "common_queries": ["inventory health", "reorder analysis", "stock optimization"]
    },
    "customer": {
        "description": "Customer master data",
        "business_context": "Core customer information for personalization and segmentation",
        "key_metrics": ["customer lifetime value", "acquisition date", "demographics"],
        "common_queries": ["customer segmentation", "lifetime value analysis", "churn prediction"]
    },
    "customer_demographics": {
        "description": "Demographic attributes of customers",
        "business_context": "Used for targeted marketing and customer profiling",
        "key_metrics": ["age groups", "income levels", "family composition"],
        "common_queries": ["demographic analysis", "target audience", "customer profiles"]
    },
    "customer_address": {
        "description": "Geographic location of customers",
        "business_context": "Enables geographic analysis and regional marketing",
        "key_metrics": ["geographic distribution", "regional trends"],
        "common_queries": ["sales by region", "geographic expansion", "location-based marketing"]
    },
    "date_dim": {
        "description": "Date dimension for time-series analysis",
        "business_context": "Critical for all temporal analysis and trend identification",
        "key_metrics": ["fiscal periods", "holidays", "weekends"],
        "common_queries": ["year-over-year trends", "seasonal patterns", "holiday impact"]
    },
    "time_dim": {
        "description": "Time of day dimension",
        "business_context": "Intraday analysis for staffing and promotion timing",
        "key_metrics": ["peak hours", "shift performance"],
        "common_queries": ["hourly sales patterns", "peak shopping times", "shift analysis"]
    },
    "item": {
        "description": "Product catalog with all item details",
        "business_context": "Master product data for merchandising and inventory",
        "key_metrics": ["product categories", "brands", "price points"],
        "common_queries": ["product performance", "category analysis", "brand comparison"]
    },
    "store": {
        "description": "Store locations and attributes",
        "business_context": "Physical store master data for location-based analysis",
        "key_metrics": ["store count", "floor space", "employee count"],
        "common_queries": ["store performance", "location analysis", "expansion planning"]
    },
    "warehouse": {
        "description": "Warehouse locations and capacity",
        "business_context": "Distribution center data for supply chain analysis",
        "key_metrics": ["warehouse capacity", "utilization", "location"],
        "common_queries": ["fulfillment analysis", "capacity planning", "distribution efficiency"]
    },
    "promotion": {
        "description": "Marketing promotions and campaigns",
        "business_context": "Track promotional effectiveness and ROI",
        "key_metrics": ["promotion lift", "ROI", "participation rate"],
        "common_queries": ["promotion effectiveness", "campaign ROI", "discount impact"]
    },
    "reason": {
        "description": "Return reasons for customer returns",
        "business_context": "Understand why customers return products",
        "key_metrics": ["reason categories", "defect rates"],
        "common_queries": ["top return reasons", "quality issues", "customer satisfaction"]
    },
    "ship_mode": {
        "description": "Shipping methods and carriers",
        "business_context": "Analyze shipping costs and delivery performance",
        "key_metrics": ["shipping costs", "delivery times", "carrier performance"],
        "common_queries": ["shipping analysis", "carrier comparison", "delivery optimization"]
    },
    "call_center": {
        "description": "Call center information",
        "business_context": "Customer service operations and catalog sales support",
        "key_metrics": ["call volume", "service levels"],
        "common_queries": ["call center performance", "service quality"]
    },
    "catalog_page": {
        "description": "Catalog page information",
        "business_context": "Track which catalog pages drive sales",
        "key_metrics": ["page views", "conversion by page"],
        "common_queries": ["catalog effectiveness", "page performance"]
    },
    "web_page": {
        "description": "Website page information",
        "business_context": "Digital analytics for website optimization",
        "key_metrics": ["page views", "bounce rates", "conversions"],
        "common_queries": ["web analytics", "page optimization", "user journey"]
    },
    "web_site": {
        "description": "Website master data",
        "business_context": "Track multiple websites or site versions",
        "key_metrics": ["site traffic", "site revenue"],
        "common_queries": ["site comparison", "A/B testing results"]
    },
    "household_demographics": {
        "description": "Household-level demographic information",
        "business_context": "Family unit analysis for targeted marketing",
        "key_metrics": ["household size", "vehicle ownership", "income"],
        "common_queries": ["household segmentation", "family buying patterns"]
    },
    "income_band": {
        "description": "Income range classifications",
        "business_context": "Income segmentation for pricing and targeting",
        "key_metrics": ["income brackets", "purchasing power"],
        "common_queries": ["income-based segmentation", "price sensitivity"]
    }
}

# Key relationships between tables
TABLE_RELATIONSHIPS = {
    "store_sales": [
        ("ss_sold_date_sk", "date_dim", "d_date_sk", "Date of sale"),
        ("ss_customer_sk", "customer", "c_customer_sk", "Customer who made purchase"),
        ("ss_item_sk", "item", "i_item_sk", "Product sold"),
        ("ss_store_sk", "store", "s_store_sk", "Store location"),
        ("ss_promo_sk", "promotion", "p_promo_sk", "Applied promotion"),
    ],
    "catalog_sales": [
        ("cs_sold_date_sk", "date_dim", "d_date_sk", "Date of sale"),
        ("cs_bill_customer_sk", "customer", "c_customer_sk", "Billing customer"),
        ("cs_ship_customer_sk", "customer", "c_customer_sk", "Shipping customer"),
        ("cs_item_sk", "item", "i_item_sk", "Product sold"),
        ("cs_warehouse_sk", "warehouse", "w_warehouse_sk", "Fulfillment warehouse"),
    ],
    "web_sales": [
        ("ws_sold_date_sk", "date_dim", "d_date_sk", "Date of sale"),
        ("ws_bill_customer_sk", "customer", "c_customer_sk", "Billing customer"),
        ("ws_item_sk", "item", "i_item_sk", "Product sold"),
        ("ws_web_page_sk", "web_page", "wp_web_page_sk", "Landing page"),
    ],
    "customer": [
        ("c_current_addr_sk", "customer_address", "ca_address_sk", "Current address"),
        ("c_current_cdemo_sk", "customer_demographics", "cd_demo_sk", "Demographics"),
        ("c_current_hdemo_sk", "household_demographics", "hd_demo_sk", "Household info"),
    ]
}


def get_table_info(conn: duckdb.DuckDBPyConnection, table_name: str) -> Dict[str, Any]:
    """Get detailed information about a table"""
    try:
        # Get column information
        columns = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        
        # Get row count
        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        
        # Get sample data
        sample_data = conn.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
        
        column_info = []
        for col in columns:
            column_info.append({
                "name": col[1],
                "type": col[2],
                "nullable": not col[3]
            })
        
        return {
            "name": table_name,
            "row_count": row_count,
            "columns": column_info,
            "sample_data": sample_data[:3] if sample_data else []
        }
    except Exception as e:
        print(f"  ⚠️  Warning: Could not get info for {table_name}: {e}")
        return None


def generate_schema_overview(conn: duckdb.DuckDBPyConnection, output_dir: Path):
    """Generate overall schema documentation"""
    doc = "# TPC-DS Schema Overview\n\n"
    doc += "Comprehensive guide to the TPC-DS benchmark schema for retail analytics.\n\n"
    
    doc += "## Schema Summary\n\n"
    doc += "TPC-DS models a retail data warehouse with multiple sales channels:\n"
    doc += "- **Store Sales**: Physical retail locations\n"
    doc += "- **Catalog Sales**: Mail-order catalog\n"
    doc += "- **Web Sales**: Online e-commerce\n\n"
    
    doc += "### Fact Tables (Transaction Data)\n\n"
    fact_tables = ["store_sales", "store_returns", "catalog_sales", "catalog_returns", 
                   "web_sales", "web_returns", "inventory"]
    
    for table in fact_tables:
        if table in TABLE_DESCRIPTIONS:
            desc = TABLE_DESCRIPTIONS[table]
            info = get_table_info(conn, table)
            if info:
                doc += f"#### {table}\n"
                doc += f"- **Description**: {desc['description']}\n"
                doc += f"- **Business Context**: {desc['business_context']}\n"
                doc += f"- **Row Count**: {info['row_count']:,}\n"
                doc += f"- **Key Metrics**: {', '.join(desc['key_metrics'])}\n\n"
    
    doc += "### Dimension Tables (Reference Data)\n\n"
    dimension_tables = [t for t in TABLE_DESCRIPTIONS.keys() if t not in fact_tables]
    
    for table in sorted(dimension_tables):
        desc = TABLE_DESCRIPTIONS[table]
        info = get_table_info(conn, table)
        if info:
            doc += f"#### {table}\n"
            doc += f"- **Description**: {desc['description']}\n"
            doc += f"- **Row Count**: {info['row_count']:,}\n\n"
    
    # Save document
    with open(output_dir / "schema_overview.md", "w") as f:
        f.write(doc)
    
    print("  ✅ Created schema_overview.md")


def generate_table_details(conn: duckdb.DuckDBPyConnection, output_dir: Path):
    """Generate detailed documentation for each table"""
    tables_dir = output_dir / "tables"
    tables_dir.mkdir(exist_ok=True)
    
    tables = conn.execute("SHOW TABLES").fetchall()
    
    for (table_name,) in tables:
        info = get_table_info(conn, table_name)
        if not info:
            continue
        
        doc = f"# {table_name}\n\n"
        
        # Add description
        if table_name in TABLE_DESCRIPTIONS:
            desc = TABLE_DESCRIPTIONS[table_name]
            doc += f"## Description\n\n{desc['description']}\n\n"
            doc += f"## Business Context\n\n{desc['business_context']}\n\n"
            
            if 'key_metrics' in desc:
                doc += f"## Key Metrics\n\n"
                for metric in desc['key_metrics']:
                    doc += f"- {metric}\n"
                doc += "\n"
            
            if 'common_queries' in desc:
                doc += f"## Common Use Cases\n\n"
                for query in desc['common_queries']:
                    doc += f"- {query}\n"
                doc += "\n"
        
        # Add row count
        doc += f"## Statistics\n\n"
        doc += f"- **Total Rows**: {info['row_count']:,}\n\n"
        
        # Add column information
        doc += f"## Columns\n\n"
        doc += "| Column Name | Data Type | Description |\n"
        doc += "|-------------|-----------|-------------|\n"
        
        for col in info['columns']:
            doc += f"| {col['name']} | {col['type']} | |\n"
        
        doc += "\n"
        
        # Add relationships
        if table_name in TABLE_RELATIONSHIPS:
            doc += f"## Relationships\n\n"
            for fk_col, ref_table, ref_col, description in TABLE_RELATIONSHIPS[table_name]:
                doc += f"- **{fk_col}** → {ref_table}.{ref_col}: {description}\n"
            doc += "\n"
        
        # Add sample queries
        doc += f"## Example Queries\n\n"
        doc += f"### Row Count\n```sql\n"
        doc += f"SELECT COUNT(*) FROM {table_name};\n```\n\n"
        
        if info['columns']:
            first_col = info['columns'][0]['name']
            doc += f"### Sample Data\n```sql\n"
            doc += f"SELECT * FROM {table_name} LIMIT 10;\n```\n\n"
        
        # Save document
        with open(tables_dir / f"{table_name}.md", "w") as f:
            f.write(doc)
    
    print(f"  ✅ Created {len(tables)} table documents")


def generate_query_patterns(output_dir: Path):
    """Generate common query patterns and examples"""
    doc = "# Common Query Patterns\n\n"
    doc += "SQL query patterns for typical analytical questions.\n\n"
    
    patterns = {
        "Sales Analysis": [
            {
                "question": "What are total sales by year?",
                "sql": """
SELECT 
    d.d_year,
    SUM(ss.ss_sales_price) as total_sales
FROM store_sales ss
JOIN date_dim d ON ss.ss_sold_date_sk = d.d_date_sk
GROUP BY d.d_year
ORDER BY d.d_year;
"""
            },
            {
                "question": "Top 10 products by revenue",
                "sql": """
SELECT 
    i.i_product_name,
    SUM(ss.ss_sales_price) as revenue
FROM store_sales ss
JOIN item i ON ss.ss_item_sk = i.i_item_sk
GROUP BY i.i_product_name
ORDER BY revenue DESC
LIMIT 10;
"""
            }
        ],
        "Customer Analysis": [
            {
                "question": "Customer lifetime value by demographic",
                "sql": """
SELECT 
    cd.cd_gender,
    cd.cd_education_status,
    COUNT(DISTINCT c.c_customer_sk) as customer_count,
    SUM(ss.ss_sales_price) as total_value
FROM customer c
JOIN customer_demographics cd ON c.c_current_cdemo_sk = cd.cd_demo_sk
JOIN store_sales ss ON c.c_customer_sk = ss.ss_customer_sk
GROUP BY cd.cd_gender, cd.cd_education_status
ORDER BY total_value DESC;
"""
            }
        ],
        "Time Series": [
            {
                "question": "Monthly sales trend with year-over-year comparison",
                "sql": """
SELECT 
    d.d_year,
    d.d_moy as month,
    SUM(ss.ss_sales_price) as monthly_sales,
    LAG(SUM(ss.ss_sales_price), 12) OVER (ORDER BY d.d_year, d.d_moy) as prior_year_sales
FROM store_sales ss
JOIN date_dim d ON ss.ss_sold_date_sk = d.d_date_sk
GROUP BY d.d_year, d.d_moy
ORDER BY d.d_year, d.d_moy;
"""
            }
        ],
        "Product Analysis": [
            {
                "question": "Products with high return rates",
                "sql": """
SELECT 
    i.i_product_name,
    COUNT(DISTINCT ss.ss_ticket_number) as sales_count,
    COUNT(DISTINCT sr.sr_ticket_number) as return_count,
    ROUND(100.0 * COUNT(DISTINCT sr.sr_ticket_number) / COUNT(DISTINCT ss.ss_ticket_number), 2) as return_rate
FROM store_sales ss
JOIN item i ON ss.ss_item_sk = i.i_item_sk
LEFT JOIN store_returns sr ON ss.ss_item_sk = sr.sr_item_sk 
    AND ss.ss_ticket_number = sr.sr_ticket_number
GROUP BY i.i_product_name
HAVING COUNT(DISTINCT ss.ss_ticket_number) > 100
ORDER BY return_rate DESC
LIMIT 20;
"""
            }
        ]
    }
    
    for category, queries in patterns.items():
        doc += f"## {category}\n\n"
        for i, query in enumerate(queries, 1):
            doc += f"### {i}. {query['question']}\n\n"
            doc += f"```sql{query['sql']}```\n\n"
    
    with open(output_dir / "query_patterns.md", "w") as f:
        f.write(doc)
    
    print("  ✅ Created query_patterns.md")


def generate_data_format_conversions(conn: duckdb.DuckDBPyConnection, output_dir: Path):
    """Generate documentation for common data format conversions."""
    print("   • Data format conversions...")
    
    content = """# Data Format Conversion Guide

## Common Data Format Patterns and SQL Conversions

This document provides SQL conversion patterns for common data formats found in TPC-DS and similar datasets.

### Date and Time Formats

#### 1. Julian Day Numbers (Surrogate Keys)
**Pattern:** Integer values like `2451822`, `2451521`, `2459000`
**Found in:** `*_date_sk` columns (e.g., `sr_returned_date_sk`, `ss_sold_date_sk`)
**What it is:** Surrogate key representing days since January 1, 4713 BC (Julian calendar)

**SQL Conversion (DuckDB/SQLite):**
```sql
-- Convert Julian Day surrogate key to readable date
SELECT DATE(date_sk - 2440588) as readable_date
FROM table_name;

-- Example:
SELECT 
    sr_ticket_number,
    sr_returned_date_sk as julian_day,
    DATE(sr_returned_date_sk - 2440588) as return_date
FROM store_returns
WHERE sr_returned_date_sk IS NOT NULL
LIMIT 5;
```

**Why subtract 2440588?**
- Unix epoch (1970-01-01) corresponds to Julian Day 2440588
- This converts Julian Day to Unix-based date system used by SQL

#### 2. Time Surrogate Keys
**Pattern:** Integer values like `28800`, `43200`, `64800`
**Found in:** `*_time_sk` columns (e.g., `sr_return_time_sk`, `ss_sold_time_sk`)
**What it is:** Seconds since midnight

**SQL Conversion:**
```sql
-- Convert time_sk to readable time (HH:MM:SS)
SELECT 
    printf('%02d:%02d:%02d', 
        time_sk / 3600,
        (time_sk % 3600) / 60,
        time_sk % 60
    ) as readable_time
FROM table_name;

-- Example:
SELECT 
    sr_ticket_number,
    sr_return_time_sk as seconds,
    printf('%02d:%02d:%02d', 
        sr_return_time_sk / 3600,
        (sr_return_time_sk % 3600) / 60,
        sr_return_time_sk % 60
    ) as return_time
FROM store_returns
WHERE sr_return_time_sk IS NOT NULL
LIMIT 5;
```

### TPC-DS Specific Format Examples
"""
    
    # Get actual date ranges from the database
    try:
        date_stats = conn.execute("""
            SELECT 
                MIN(sr_returned_date_sk) as min_date_sk,
                MAX(sr_returned_date_sk) as max_date_sk,
                DATE(MIN(sr_returned_date_sk) - 2440588) as min_readable_date,
                DATE(MAX(sr_returned_date_sk) - 2440588) as max_readable_date
            FROM store_returns
            WHERE sr_returned_date_sk IS NOT NULL
        """).fetchone()
        
        if date_stats:
            content += f"""
#### Actual Date Range in Database

**Store Returns Date Range:**
- Surrogate Keys: {date_stats[0]} to {date_stats[1]}
- Readable Dates: {date_stats[2]} to {date_stats[3]}

"""
    except Exception as e:
        print(f"      Warning: Could not fetch date stats: {e}")
    
    content += """
### Complete Conversion Examples

#### All Returns with Readable Dates
```sql
-- Combine all return types with date conversions
SELECT 
    'store' as return_type,
    sr_ticket_number as ticket_number,
    DATE(sr_returned_date_sk - 2440588) as return_date,
    printf('%02d:%02d:%02d', 
        sr_return_time_sk / 3600,
        (sr_return_time_sk % 3600) / 60,
        sr_return_time_sk % 60
    ) as return_time,
    sr_return_amt as return_amount
FROM store_returns
WHERE sr_returned_date_sk IS NOT NULL

UNION ALL

SELECT 
    'catalog' as return_type,
    cr_order_number as ticket_number,
    DATE(cr_returned_date_sk - 2440588) as return_date,
    printf('%02d:%02d:%02d', 
        cr_returned_time_sk / 3600,
        (cr_returned_time_sk % 3600) / 60,
        cr_returned_time_sk % 60
    ) as return_time,
    cr_return_amount as return_amount
FROM catalog_returns
WHERE cr_returned_date_sk IS NOT NULL

UNION ALL

SELECT 
    'web' as return_type,
    wr_order_number as ticket_number,
    DATE(wr_returned_date_sk - 2440588) as return_date,
    printf('%02d:%02d:%02d', 
        wr_returned_time_sk / 3600,
        (wr_returned_time_sk % 3600) / 60,
        wr_returned_time_sk % 60
    ) as return_time,
    wr_return_amt as return_amount
FROM web_returns
WHERE wr_returned_date_sk IS NOT NULL

ORDER BY return_date DESC
LIMIT 1000;
```

#### Sales with Readable Dates
```sql
-- Most recent sales with readable dates and times
SELECT 
    ss_sold_date_sk as date_surrogate,
    DATE(ss_sold_date_sk - 2440588) as sale_date,
    printf('%02d:%02d:%02d', 
        ss_sold_time_sk / 3600,
        (ss_sold_time_sk % 3600) / 60,
        ss_sold_time_sk % 60
    ) as sale_time,
    ss_item_sk as item_id,
    ss_quantity,
    ss_sales_price
FROM store_sales
WHERE ss_sold_date_sk IS NOT NULL
ORDER BY ss_sold_date_sk DESC, ss_sold_time_sk DESC
LIMIT 100;
```

### Best Practices

1. **Always check for NULL values** before converting surrogate keys
   ```sql
   WHERE date_sk IS NOT NULL
   ```

2. **Use meaningful aliases** for converted columns
   ```sql
   DATE(sr_returned_date_sk - 2440588) as return_date
   ```

3. **Validate date ranges** - TPC-DS typically uses dates from 1998-2003
   ```sql
   WHERE DATE(date_sk - 2440588) BETWEEN '1998-01-01' AND '2003-12-31'
   ```

4. **Join with date_dim** for more date attributes
   ```sql
   SELECT 
       sr.sr_ticket_number,
       d.d_date as return_date,
       d.d_day_name,
       d.d_week_seq,
       sr.sr_return_amt
   FROM store_returns sr
   JOIN date_dim d ON sr.sr_returned_date_sk = d.d_date_sk
   ```

### Common Pitfalls

❌ **Don't do this:**
```sql
-- Forgetting NULL check (will error)
SELECT DATE(sr_returned_date_sk - 2440588) FROM store_returns;

-- Using wrong constant
SELECT DATE(sr_returned_date_sk) FROM store_returns;
-- Results in dates thousands of years in the past!

-- Not checking date ranges
SELECT DATE(invalid_sk - 2440588) FROM table;
-- Could produce dates like year 1000 or year 5000
```

✅ **Do this:**
```sql
-- Proper NULL handling
SELECT DATE(sr_returned_date_sk - 2440588) 
FROM store_returns 
WHERE sr_returned_date_sk IS NOT NULL;

-- With validation
SELECT DATE(sr_returned_date_sk - 2440588) as return_date
FROM store_returns 
WHERE sr_returned_date_sk IS NOT NULL
  AND sr_returned_date_sk > 2450000  -- Reasonable date range
  AND sr_returned_date_sk < 2460000;
```

### When to Use Surrogate Keys vs Date Dimension

**Use Surrogate Keys directly when:**
- Need quick date filtering
- Don't need date attributes (day name, week, quarter, etc.)
- Performing date arithmetic

**Use Date Dimension (date_dim) when:**
- Need date attributes (fiscal year, holiday indicator, etc.)
- Doing calendar-based analysis
- Need standardized date formats

### Example: Combining Both Approaches
```sql
-- Get returns with both converted dates AND date attributes
SELECT 
    sr.sr_ticket_number,
    DATE(sr.sr_returned_date_sk - 2440588) as return_date_converted,
    d.d_date as return_date_from_dim,
    d.d_day_name,
    d.d_qoy as quarter,
    d.d_holiday as is_holiday,
    sr.sr_return_amt
FROM store_returns sr
LEFT JOIN date_dim d ON sr.sr_returned_date_sk = d.d_date_sk
WHERE sr.sr_returned_date_sk IS NOT NULL
ORDER BY sr.sr_returned_date_sk DESC
LIMIT 100;
```
"""
    
    # Write to file
    output_file = output_dir / "data_format_conversions.md"
    output_file.write_text(content)
    print(f"      ✓ Generated {output_file.name}")


def generate_join_best_practices(output_dir: Path):
    """Generate JOIN best practices guide for TPC-DS schema"""
    doc = "# JOIN Best Practices for TPC-DS Schema\n\n"
    doc += "## Overview\n\n"
    doc += "The TPC-DS schema uses **surrogate keys** (IDs ending in `_sk`) to link fact tables with dimension tables. "
    doc += "Always JOIN dimension tables to get human-readable values instead of showing raw IDs.\n\n"
    
    doc += "## Key Principle\n\n"
    doc += "**ALWAYS join dimension tables when querying fact tables** to provide meaningful, readable results.\n\n"
    doc += "❌ **Bad**: `SELECT customer_sk, sold_date_sk FROM store_sales`  \n"
    doc += "✅ **Good**: `SELECT c.customer_id, c.first_name, d.d_date FROM store_sales s "
    doc += "JOIN customer c ON s.ss_customer_sk = c.c_customer_sk "
    doc += "JOIN date_dim d ON s.ss_sold_date_sk = d.d_date_sk`\n\n"
    
    doc += "## Common Dimension Tables and Their Keys\n\n"
    
    doc += "### Date Dimensions\n"
    doc += "- **date_dim** (d_date_sk) → Use for ANY date key:\n"
    doc += "  - `ss_sold_date_sk`, `sr_returned_date_sk`, `cs_sold_date_sk`, `ws_sold_date_sk`\n"
    doc += "  - Provides: `d_date`, `d_year`, `d_month_seq`, `d_day_name`, `d_quarter_name`\n\n"
    doc += "```sql\n"
    doc += "-- Example: Convert date keys to actual dates\n"
    doc += "SELECT \n"
    doc += "    d.d_date,\n"
    doc += "    d.d_year,\n"
    doc += "    d.d_month_seq,\n"
    doc += "    COUNT(*) as transactions\n"
    doc += "FROM store_sales ss\n"
    doc += "JOIN date_dim d ON ss.ss_sold_date_sk = d.d_date_sk\n"
    doc += "GROUP BY d.d_date, d.d_year, d.d_month_seq;\n"
    doc += "```\n\n"
    
    doc += "### Customer Dimensions\n"
    doc += "- **customer** (c_customer_sk) → Basic customer info\n"
    doc += "  - Provides: `c_customer_id`, `c_first_name`, `c_last_name`, `c_email_address`, `c_birth_country`\n"
    doc += "- **customer_demographics** (cd_demo_sk) → Demographic details\n"
    doc += "  - Provides: `cd_gender`, `cd_marital_status`, `cd_education_status`, `cd_credit_rating`\n"
    doc += "- **customer_address** (ca_address_sk) → Address info\n"
    doc += "  - Provides: `ca_street_name`, `ca_city`, `ca_state`, `ca_zip`, `ca_country`\n\n"
    doc += "```sql\n"
    doc += "-- Example: Enrich customer data\n"
    doc += "SELECT \n"
    doc += "    c.c_customer_id,\n"
    doc += "    c.c_first_name || ' ' || c.c_last_name as full_name,\n"
    doc += "    cd.cd_gender,\n"
    doc += "    cd.cd_education_status,\n"
    doc += "    ca.ca_city,\n"
    doc += "    ca.ca_state\n"
    doc += "FROM store_sales ss\n"
    doc += "JOIN customer c ON ss.ss_customer_sk = c.c_customer_sk\n"
    doc += "JOIN customer_demographics cd ON c.c_current_cdemo_sk = cd.cd_demo_sk\n"
    doc += "JOIN customer_address ca ON c.c_current_addr_sk = ca.ca_address_sk;\n"
    doc += "```\n\n"
    
    doc += "### Product/Item Dimensions\n"
    doc += "- **item** (i_item_sk) → Product details\n"
    doc += "  - Provides: `i_item_id`, `i_item_desc`, `i_brand`, `i_class`, `i_category`, `i_product_name`, `i_color`, `i_size`\n\n"
    doc += "```sql\n"
    doc += "-- Example: Show product details\n"
    doc += "SELECT \n"
    doc += "    i.i_product_name,\n"
    doc += "    i.i_brand,\n"
    doc += "    i.i_category,\n"
    doc += "    i.i_color,\n"
    doc += "    SUM(ss.ss_quantity) as units_sold\n"
    doc += "FROM store_sales ss\n"
    doc += "JOIN item i ON ss.ss_item_sk = i.i_item_sk\n"
    doc += "GROUP BY i.i_product_name, i.i_brand, i.i_category, i.i_color;\n"
    doc += "```\n\n"
    
    doc += "### Store Dimensions\n"
    doc += "- **store** (s_store_sk) → Store information\n"
    doc += "  - Provides: `s_store_id`, `s_store_name`, `s_number_employees`, `s_city`, `s_state`, `s_zip`\n\n"
    doc += "```sql\n"
    doc += "-- Example: Sales by store\n"
    doc += "SELECT \n"
    doc += "    s.s_store_name,\n"
    doc += "    s.s_city,\n"
    doc += "    s.s_state,\n"
    doc += "    COUNT(*) as transactions,\n"
    doc += "    SUM(ss.ss_sales_price) as revenue\n"
    doc += "FROM store_sales ss\n"
    doc += "JOIN store s ON ss.ss_store_sk = s.s_store_sk\n"
    doc += "GROUP BY s.s_store_name, s.s_city, s.s_state;\n"
    doc += "```\n\n"
    
    doc += "### Time Dimensions\n"
    doc += "- **time_dim** (t_time_sk) → Time of day\n"
    doc += "  - Provides: `t_time`, `t_hour`, `t_minute`, `t_am_pm`, `t_shift`, `t_meal_time`\n\n"
    doc += "```sql\n"
    doc += "-- Example: Sales by time of day\n"
    doc += "SELECT \n"
    doc += "    t.t_hour,\n"
    doc += "    t.t_am_pm,\n"
    doc += "    t.t_shift,\n"
    doc += "    COUNT(*) as transactions\n"
    doc += "FROM store_sales ss\n"
    doc += "JOIN time_dim t ON ss.ss_sold_time_sk = t.t_time_sk\n"
    doc += "GROUP BY t.t_hour, t.t_am_pm, t.t_shift;\n"
    doc += "```\n\n"
    
    doc += "### Promotion Dimensions\n"
    doc += "- **promotion** (p_promo_sk) → Promotion details\n"
    doc += "  - Provides: `p_promo_id`, `p_promo_name`, `p_channel_email`, `p_channel_tv`, `p_discount_active`\n\n"
    
    doc += "### Warehouse Dimensions\n"
    doc += "- **warehouse** (w_warehouse_sk) → Warehouse info\n"
    doc += "  - Provides: `w_warehouse_id`, `w_warehouse_name`, `w_city`, `w_state`\n\n"
    
    doc += "## Fact Tables and Their Common JOINs\n\n"
    doc += "### store_sales (Most Common)\n"
    doc += "```sql\n"
    doc += "SELECT \n"
    doc += "    -- Date\n"
    doc += "    d.d_date,\n"
    doc += "    d.d_year,\n"
    doc += "    -- Customer\n"
    doc += "    c.c_customer_id,\n"
    doc += "    c.c_first_name,\n"
    doc += "    c.c_last_name,\n"
    doc += "    -- Product\n"
    doc += "    i.i_product_name,\n"
    doc += "    i.i_brand,\n"
    doc += "    i.i_category,\n"
    doc += "    -- Store\n"
    doc += "    s.s_store_name,\n"
    doc += "    s.s_city,\n"
    doc += "    -- Metrics\n"
    doc += "    ss.ss_quantity,\n"
    doc += "    ss.ss_sales_price\n"
    doc += "FROM store_sales ss\n"
    doc += "LEFT JOIN date_dim d ON ss.ss_sold_date_sk = d.d_date_sk\n"
    doc += "LEFT JOIN customer c ON ss.ss_customer_sk = c.c_customer_sk\n"
    doc += "LEFT JOIN item i ON ss.ss_item_sk = i.i_item_sk\n"
    doc += "LEFT JOIN store s ON ss.ss_store_sk = s.s_store_sk\n"
    doc += "LIMIT 100;\n"
    doc += "```\n\n"
    
    doc += "### store_returns\n"
    doc += "```sql\n"
    doc += "SELECT \n"
    doc += "    -- Date\n"
    doc += "    d.d_date as return_date,\n"
    doc += "    -- Customer\n"
    doc += "    c.c_customer_id,\n"
    doc += "    c.c_first_name,\n"
    doc += "    -- Product\n"
    doc += "    i.i_product_name,\n"
    doc += "    -- Store\n"
    doc += "    s.s_store_name,\n"
    doc += "    -- Return info\n"
    doc += "    sr.sr_return_quantity,\n"
    doc += "    sr.sr_return_amt\n"
    doc += "FROM store_returns sr\n"
    doc += "LEFT JOIN date_dim d ON sr.sr_returned_date_sk = d.d_date_sk\n"
    doc += "LEFT JOIN customer c ON sr.sr_customer_sk = c.c_customer_sk\n"
    doc += "LEFT JOIN item i ON sr.sr_item_sk = i.i_item_sk\n"
    doc += "LEFT JOIN store s ON sr.sr_store_sk = s.s_store_sk\n"
    doc += "LIMIT 100;\n"
    doc += "```\n\n"
    
    doc += "### catalog_sales & web_sales\n"
    doc += "Similar patterns - join with:\n"
    doc += "- `date_dim` for dates\n"
    doc += "- `customer` for customer info\n"
    doc += "- `item` for products\n"
    doc += "- `warehouse` for fulfillment location\n"
    doc += "- `ship_mode` for shipping details\n\n"
    
    doc += "## Default Query Template\n\n"
    doc += "When user asks to \"show\" or \"get\" data from a fact table, ALWAYS use this pattern:\n\n"
    doc += "```sql\n"
    doc += "SELECT \n"
    doc += "    -- Always include dimension values, not just keys\n"
    doc += "    d.d_date,\n"
    doc += "    c.c_customer_id,\n"
    doc += "    i.i_product_name,\n"
    doc += "    s.s_store_name,\n"
    doc += "    -- Include metrics from fact table\n"
    doc += "    fact.quantity_column,\n"
    doc += "    fact.amount_column\n"
    doc += "FROM {fact_table} fact\n"
    doc += "LEFT JOIN date_dim d ON fact.date_sk_column = d.d_date_sk\n"
    doc += "LEFT JOIN customer c ON fact.customer_sk_column = c.c_customer_sk\n"
    doc += "LEFT JOIN item i ON fact.item_sk_column = i.i_item_sk\n"
    doc += "LEFT JOIN store s ON fact.store_sk_column = s.s_store_sk\n"
    doc += "WHERE {conditions}\n"
    doc += "ORDER BY {sort_columns}\n"
    doc += "LIMIT {row_limit};\n"
    doc += "```\n\n"
    
    doc += "## Common Mistakes to Avoid\n\n"
    doc += "❌ **Returning surrogate keys without dimension joins**:\n"
    doc += "```sql\n"
    doc += "-- BAD: Users see meaningless IDs\n"
    doc += "SELECT ss_customer_sk, ss_item_sk, ss_sold_date_sk \n"
    doc += "FROM store_sales;\n"
    doc += "```\n\n"
    doc += "✅ **Always join dimensions**:\n"
    doc += "```sql\n"
    doc += "-- GOOD: Users see meaningful values\n"
    doc += "SELECT c.c_customer_id, i.i_product_name, d.d_date\n"
    doc += "FROM store_sales ss\n"
    doc += "JOIN customer c ON ss.ss_customer_sk = c.c_customer_sk\n"
    doc += "JOIN item i ON ss.ss_item_sk = i.i_item_sk\n"
    doc += "JOIN date_dim d ON ss.ss_sold_date_sk = d.d_date_sk;\n"
    doc += "```\n\n"
    doc += "❌ **Forgetting date dimensions**:\n"
    doc += "```sql\n"
    doc += "-- BAD: Date keys are not human readable\n"
    doc += "SELECT ss_sold_date_sk FROM store_sales;\n"
    doc += "```\n\n"
    doc += "✅ **Always convert date keys**:\n"
    doc += "```sql\n"
    doc += "-- GOOD: Actual dates shown\n"
    doc += "SELECT d.d_date, d.d_year \n"
    doc += "FROM store_sales ss\n"
    doc += "JOIN date_dim d ON ss.ss_sold_date_sk = d.d_date_sk;\n"
    doc += "```\n\n"
    
    doc += "## Summary\n\n"
    doc += "**Golden Rule**: Never return surrogate keys (`_sk` columns) directly. "
    doc += "Always JOIN dimension tables to provide meaningful, human-readable results.\n"
    
    # Write to file
    output_file = output_dir / "join_best_practices.md"
    output_file.write_text(doc)
    print(f"      ✓ Generated {output_file.name}")


def generate_business_glossary(output_dir: Path):
    """Generate business terminology glossary"""
    doc = "# Business Glossary\n\n"
    doc += "Common business terms and metrics used in retail analytics.\n\n"
    
    glossary = {
        "Revenue/Sales Metrics": {
            "Total Sales": "Sum of all sales prices (ss_sales_price)",
            "Net Sales": "Sales after returns and discounts",
            "Gross Profit": "Sales minus cost (ss_sales_price - ss_wholesale_cost)",
            "Net Profit": "ss_net_profit field (includes all costs and discounts)"
        },
        "Customer Metrics": {
            "Customer Lifetime Value (CLV)": "Total revenue from a customer over their lifetime",
            "Customer Acquisition Date": "c_first_sales_date_sk",
            "Active Customer": "Customer with purchase in analysis period",
            "Churn": "Customer with no recent purchases"
        },
        "Product Metrics": {
            "SKU": "Stock Keeping Unit - unique product identifier",
            "Category": "Product category (i_category)",
            "Brand": "Product brand (i_brand)",
            "Return Rate": "Percentage of items returned"
        },
        "Time Periods": {
            "Fiscal Year": "d_fy_year",
            "Quarter": "3-month period",
            "Week": "7-day period starting Sunday",
            "Holiday": "Special day indicated by d_holiday"
        },
        "Channel Metrics": {
            "Store Sales": "Physical retail location sales",
            "Catalog Sales": "Mail-order sales",
            "Web Sales": "Online e-commerce sales",
            "Omnichannel": "All channels combined"
        }
    }
    
    for category, terms in glossary.items():
        doc += f"## {category}\n\n"
        for term, definition in terms.items():
            doc += f"### {term}\n{definition}\n\n"
    
    with open(output_dir / "business_glossary.md", "w") as f:
        f.write(doc)
    
    print("  ✅ Created business_glossary.md")


def main():
    parser = argparse.ArgumentParser(description="Generate RAG documents from TPC-DS schema")
    parser.add_argument("--db-path", type=str, default="tpcds_1gb.duckdb", help="DuckDB database path")
    parser.add_argument("--output-dir", type=str, default="rag_documents", help="Output directory")
    args = parser.parse_args()
    
    db_path = Path(args.db_path)
    output_dir = Path(args.output_dir)
    
    print("📚 Generating RAG Documents")
    print("="*60)
    print(f"Database: {db_path}")
    print(f"Output: {output_dir}")
    print("="*60)
    
    if not db_path.exists():
        print(f"\n❌ Error: Database not found: {db_path}")
        print("Run setup_tpcds_duckdb.py first!")
        return
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Connect to database
    print("\n🔌 Connecting to database...")
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Generate documents
    print("\n📝 Generating documents...")
    
    generate_schema_overview(conn, output_dir)
    generate_table_details(conn, output_dir)
    generate_query_patterns(output_dir)
    generate_data_format_conversions(conn, output_dir)
    generate_join_best_practices(output_dir)
    generate_business_glossary(output_dir)
    
    # Close connection
    conn.close()
    
    # Count files
    file_count = len(list(output_dir.rglob("*.md")))
    
    print("\n" + "="*60)
    print("✅ RAG document generation complete!")
    print("="*60)
    print(f"\n📊 Generated {file_count} markdown files")
    print(f"📁 Location: {output_dir}")
    
    print("\n🎯 Next steps:")
    print("   1. Load documents into vector store:")
    print(f"      python ../examples/vector_store_example.py --docs {output_dir}")
    print("   2. Test RAG-assisted queries:")
    print("      python run_performance_tests.py --rag-enabled")


if __name__ == "__main__":
    main()
