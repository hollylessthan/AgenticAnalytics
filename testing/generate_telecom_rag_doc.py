import duckdb
import pandas as pd
import os

# Connect to DuckDB and read the telecom table
con = duckdb.connect('testing/telecom.duckdb')
df = con.execute('SELECT * FROM telecom').df()
con.close()

# Prepare markdown doc in schema_overview.md style
row_count = len(df)

doc = """# Telecom Dataset Overview

Comprehensive guide to the simulated telecom customer analytics dataset.

## Table Summary

### telecom
- **Description**: Simulated telecom customer data for analytics and modeling
- **Business Context**: Contains customer tenure, demographics, usage, billing, and lifetime value for churn and value modeling
- **Row Count**: {row_count}
- **Key Metrics**: lifetime value, tenure, monthly bill, data usage, credit score

#### Columns
""".format(row_count=row_count)

column_descriptions = {
    'tenure_months': 'Customer tenure in months (exponential, right-skewed)',
    'age': 'Customer age in years (uniform distribution)',
    'avg_data_usage_gb': 'Average monthly data usage in GB (log-normal, heavy right tail)',
    'monthly_bill': 'Monthly bill amount (bimodal: low and high spenders)',
    'credit_score': 'Credit score (normal distribution)',
    'lifetime_value_target': 'Simulated customer lifetime value (target for regression)'
}

for col in df.columns:
    dtype = str(df[col].dtype)
    desc = column_descriptions.get(col, '')
    doc += f"- **{col}** ({dtype}): {desc}\n"

# Write to rag_documents/telecom_overview.md
os.makedirs('testing/rag_documents', exist_ok=True)
with open('testing/rag_documents/telecom_overview.md', 'w') as f:
    f.write(doc)
print('Telecom RAG doc generated at testing/rag_documents/telecom_overview.md')