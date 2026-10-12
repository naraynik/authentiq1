import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')

domains_dir = r"C:\Users\Monish\Downloads\Dataset for AuthentiQ\domains"
domains = ["Luxury_Items", "Packaged_Foods", "Electronics", "Fashion", "Pharmaceuticals"]

results = []

def preprocess_domain_data(df):
    # 1. Engineered Features from prior logic
    df['signup_time'] = pd.to_datetime(df['signup_time'])
    df['purchase_time'] = pd.to_datetime(df['purchase_time'])
    df['hours_since_creation'] = (df['purchase_time'] - df['signup_time']).dt.total_seconds() / 3600.0
    
    device_counts = df['device_id'].value_counts().to_dict()
    df['scan_velocity'] = df['device_id'].map(device_counts)
    
    ip_per_device = df.groupby('device_id')['ip_address'].nunique().to_dict()
    df['is_location_anomaly'] = df['device_id'].map(ip_per_device) > 1
    df['is_location_anomaly'] = df['is_location_anomaly'].astype(int)
    
    # 2. Base Features
    df = df.drop(columns=['user_id', 'signup_time', 'purchase_time', 'device_id', 'ip_address'])
    
    # One-hot encode categorical features
    df = pd.get_dummies(df, columns=['source', 'browser', 'sex'], drop_first=True)
    
    # Fill NaNs if any
    df = df.fillna(0)
    
    return df

print("="*60)
print("EVALUATING DOMAINS WITH FULL PARAMETER SET")
print("="*60)

for domain in domains:
    file_path = os.path.join(domains_dir, f"{domain}.csv")
    df = pd.read_csv(file_path)
    
    df = preprocess_domain_data(df)
    
    X = df.drop(columns=['class'])
    y = df['class']
    
    # Ensure all numerical data is correctly typed
    X = X.astype(float)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # We use a slightly smaller grid for faster evaluation, but still tuned and balanced
    base_clf = RandomForestClassifier(random_state=42, class_weight='balanced')
    param_grid = {
        'n_estimators': [100],
        'max_depth': [15, 20]
    }
    grid_search = GridSearchCV(base_clf, param_grid, cv=3, scoring='f1_macro', n_jobs=-1)
    grid_search.fit(X_train, y_train)
    
    clf = grid_search.best_estimator_
    preds = clf.predict(X_test)
    
    acc = accuracy_score(y_test, preds)
    f1 = f1_score(y_test, preds, average='macro')
    
    results.append({
        'Domain': domain.replace('_', ' '),
        'Accuracy': acc * 100,
        'F1-Score': f1 * 100,
        'Best Depth': grid_search.best_params_['max_depth']
    })
    print(f"[*] {domain} -> Acc: {acc*100:.2f}% | F1: {f1*100:.2f}%")

print("\n" + "="*60)
print("FINAL DOMAIN COMPARISON")
print("="*60)
results_df = pd.DataFrame(results)
results_df = results_df.sort_values(by='Accuracy', ascending=False).reset_index(drop=True)
print(results_df.to_string(index=False))
print("="*60)
