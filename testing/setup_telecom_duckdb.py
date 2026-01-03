import pandas as pd
import numpy as np
import duckdb

# Set random seed for reproducibility
np.random.seed(42)
n_samples = 4800

# Generate 4800 samples with specific non-normal behaviors
data = {
    'tenure_months': np.random.exponential(scale=12, size=n_samples),
    'age': np.random.randint(18, 80, size=n_samples),
    'avg_data_usage_gb': np.random.lognormal(mean=2, sigma=1, size=n_samples),
    'monthly_bill': np.concatenate([
        np.random.normal(30, 5, n_samples//2),
        np.random.normal(90, 10, n_samples//2)
    ]),
    'credit_score': np.random.normal(700, 50, n_samples)
}

df = pd.DataFrame(data)
# Shuffle the data (to remove the bimodal sorting order)
df = df.sample(frac=1).reset_index(drop=True)
# Create Target Variable (Ground Truth)
noise = np.random.normal(0, 50, n_samples)
df['lifetime_value_target'] = (
    (df['monthly_bill'] * df['tenure_months']) * 0.5 + 
    (df['avg_data_usage_gb'] * 10) + 
    (df['age'] * 2) + 
    noise
)

# Save to main DuckDB (same as database_url in config)
db_path = './testing/tpcds_1gb.duckdb'
con = duckdb.connect(db_path)
con.execute('CREATE OR REPLACE TABLE telecom AS SELECT * FROM df')
con.close()
print('Telecom dataset loaded into DuckDB at', db_path)
