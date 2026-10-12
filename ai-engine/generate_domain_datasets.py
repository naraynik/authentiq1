import pandas as pd
import numpy as np
import os
import shutil

# Set random seed for reproducibility
np.random.seed(42)

source_file = r"C:\Users\Monish\Downloads\Dataset for AuthentiQ\Fraud_Data.csv"
output_dir = r"C:\Users\Monish\Downloads\Dataset for AuthentiQ\domains"

os.makedirs(output_dir, exist_ok=True)
print(f"Loading {source_file}...")
df = pd.read_csv(source_file)

# Shuffle and split into 5 equal chunks
df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
chunks = np.array_split(df_shuffled, 5)

domains = [
    {"name": "Luxury_Items", "multiplier": 15.0, "fraud_bias": "high"},
    {"name": "Packaged_Foods", "multiplier": 0.1, "fraud_bias": "low"},
    {"name": "Electronics", "multiplier": 2.5, "feature_bias": "browser"},
    {"name": "Fashion", "multiplier": 0.8, "feature_bias": "demographic"},
    {"name": "Pharmaceuticals", "multiplier": 5.0, "feature_bias": "source"}
]

for idx, domain in enumerate(domains):
    print(f"Generating dataset for {domain['name']}...")
    chunk = chunks[idx].copy()
    
    # Apply price multiplier
    chunk['purchase_value'] = (chunk['purchase_value'] * domain['multiplier']).astype(int)
    
    if domain.get("fraud_bias") == "high":
        # Keep all fraud (1), drop 70% of authentic (0) to artificially inflate fraud rate
        authentic = chunk[chunk['class'] == 0]
        fraud = chunk[chunk['class'] == 1]
        authentic = authentic.sample(frac=0.3, random_state=42)
        chunk = pd.concat([authentic, fraud])
        
    elif domain.get("fraud_bias") == "low":
        # Keep all authentic, drop 80% of fraud
        authentic = chunk[chunk['class'] == 0]
        fraud = chunk[chunk['class'] == 1]
        fraud = fraud.sample(frac=0.2, random_state=42)
        chunk = pd.concat([authentic, fraud])
        
    elif domain.get("feature_bias") == "browser":
        # Make "Chrome" highly correlated with fraud
        # For fraud=1, randomly set browser to Chrome 90% of the time
        mask_fraud = chunk['class'] == 1
        num_fraud = mask_fraud.sum()
        new_browsers = np.where(np.random.rand(num_fraud) < 0.9, 'Chrome', chunk.loc[mask_fraud, 'browser'])
        chunk.loc[mask_fraud, 'browser'] = new_browsers
        
    elif domain.get("feature_bias") == "demographic":
        # Make younger age highly correlated with fraud in Fashion
        mask_fraud = chunk['class'] == 1
        chunk.loc[mask_fraud, 'age'] = np.random.randint(18, 25, size=mask_fraud.sum())
        
    elif domain.get("feature_bias") == "source":
        # Make "Direct" source highly correlated with fraud in Pharma
        mask_fraud = chunk['class'] == 1
        num_fraud = mask_fraud.sum()
        new_sources = np.where(np.random.rand(num_fraud) < 0.85, 'Direct', chunk.loc[mask_fraud, 'source'])
        chunk.loc[mask_fraud, 'source'] = new_sources
        
    chunk = chunk.sample(frac=1, random_state=42).reset_index(drop=True)
    out_path = os.path.join(output_dir, f"{domain['name']}.csv")
    chunk.to_csv(out_path, index=False)
    print(f"Saved {domain['name']} ({len(chunk)} rows) to {out_path}")

print("Successfully generated all 5 domain datasets!")
