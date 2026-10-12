import pandas as pd
import numpy as np
import datetime
import os

np.random.seed(42)

NUM_SAMPLES = 50000
FRAUD_RATE = 0.15  # 15% of products are counterfeit

print("Generating advanced anti-counterfeit dataset...")

# Target label
is_counterfeit = np.random.choice([0, 1], size=NUM_SAMPLES, p=[1-FRAUD_RATE, FRAUD_RATE])

# Basic info
product_ids = [f"PRD_{np.random.randint(1000, 9999)}" for _ in range(NUM_SAMPLES)]
timestamps = [datetime.datetime(2026, 1, 1) + datetime.timedelta(days=np.random.randint(0, 200), hours=np.random.randint(0, 24)) for _ in range(NUM_SAMPLES)]

# Categorical Features
locations = ["USA", "China", "Germany", "India", "Vietnam"]
origins = ["Factory_A", "Factory_B", "Factory_C", "Unknown"]
weather_conditions = ["Clear", "Rain", "Humid", "Snow"]

manufacturing_location = np.random.choice(locations, size=NUM_SAMPLES)
# Counterfeits are more likely to come from "Unknown" origin
origin = np.where(is_counterfeit == 1, 
                  np.random.choice(origins, size=NUM_SAMPLES, p=[0.1, 0.1, 0.1, 0.7]),
                  np.random.choice(origins, size=NUM_SAMPLES, p=[0.4, 0.3, 0.2, 0.1]))

weather = np.random.choice(weather_conditions, size=NUM_SAMPLES)

# Continuous Features (Normal distributions, with means shifted for counterfeits)
# Authentic items have higher integrity/alignment scores. Counterfeits have lower scores and more artifacts.
def generate_feature(mean_auth, std_auth, mean_fraud, std_fraud):
    auth_vals = np.random.normal(mean_auth, std_auth, NUM_SAMPLES)
    fraud_vals = np.random.normal(mean_fraud, std_fraud, NUM_SAMPLES)
    return np.where(is_counterfeit == 0, auth_vals, fraud_vals).clip(0, 1) # scores between 0 and 1

micro_textures = generate_feature(0.95, 0.03, 0.60, 0.15)
color_printing_patterns = generate_feature(0.92, 0.05, 0.70, 0.12)
geometric_alignment = generate_feature(0.98, 0.02, 0.65, 0.10)
surface_features = generate_feature(0.90, 0.04, 0.55, 0.18)

# Printing artifacts (higher is worse, so we reverse it or just keep it as a score where 0 = many artifacts, 1 = no artifacts)
# Let's say 1.0 means perfect (no artifacts), 0.0 means terrible artifacts.
printing_artifacts = generate_feature(0.96, 0.02, 0.40, 0.20)

frequency_features = generate_feature(0.85, 0.08, 0.50, 0.15)
color_space_metrics = generate_feature(0.94, 0.03, 0.68, 0.11)
spectral_metrics = generate_feature(0.91, 0.05, 0.55, 0.14)
qr_code_integrity = generate_feature(0.99, 0.01, 0.75, 0.15)
barcode_integrity = generate_feature(0.99, 0.01, 0.80, 0.10)
deep_learning_latent_features = generate_feature(0.88, 0.06, 0.30, 0.20)

# IoT Data (Temperature and Humidity)
# Authentic items usually stay within strict supply chain bounds (e.g. 20-25C, 40-50% humidity)
# Counterfeits might lack cold-chain or climate control
temperature = np.where(is_counterfeit == 0, 
                       np.random.normal(22.0, 1.5, NUM_SAMPLES), 
                       np.random.normal(28.0, 5.0, NUM_SAMPLES))
                       
humidity = np.where(is_counterfeit == 0, 
                    np.random.normal(45.0, 5.0, NUM_SAMPLES), 
                    np.random.normal(60.0, 15.0, NUM_SAMPLES))

# Create DataFrame
df = pd.DataFrame({
    "product_id": product_ids,
    "timestamp": timestamps,
    "manufacturing_location": manufacturing_location,
    "origin": origin,
    "weather_conditions": weather,
    "temperature": temperature,
    "humidity": humidity,
    "micro_textures": micro_textures,
    "color_printing_patterns": color_printing_patterns,
    "geometric_alignment": geometric_alignment,
    "surface_features": surface_features,
    "printing_artifacts": printing_artifacts,
    "frequency_features": frequency_features,
    "color_space_metrics": color_space_metrics,
    "spectral_metrics": spectral_metrics,
    "deep_learning_latent_features": deep_learning_latent_features,
    "qr_code_integrity": qr_code_integrity,
    "barcode_integrity": barcode_integrity,
    "is_counterfeit": is_counterfeit
})

output_dir = r"C:\Users\Monish\Downloads\Dataset for AuthentiQ"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "authentiq_advanced_dataset.csv")

df.to_csv(output_path, index=False)
print(f"Generated {NUM_SAMPLES} rows of advanced optical/IoT anti-counterfeiting data!")
print(f"Saved to: {output_path}")
