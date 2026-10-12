import os
import shutil
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, precision_score, recall_score, f1_score
import joblib

try:
    import torch
    import torch.nn.functional as F
    import torch.nn as nn
    from torch_geometric.data import Data
    from torch_geometric.nn import GCNConv
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

FRAUD_DATASET_PATH = r"C:\Users\Monish\Downloads\Dataset for AuthentiQ\Fraud_Data.csv"
BACKEND_MODEL_DIR = os.path.join("..", "backend", "app", "models")

class LeakageFreePipeline:
    def __init__(self):
        self.device_counts = {}
        self.device_ips = {}
        self.ip_devices = {}

    def fit(self, df_train: pd.DataFrame):
        self.device_counts = df_train['device_id'].value_counts().to_dict()
        self.device_ips = df_train.groupby('device_id')['ip_address'].nunique().to_dict()
        self.ip_devices = df_train.groupby('ip_address')['device_id'].nunique().to_dict()

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame(index=df.index)
        signup_dt = pd.to_datetime(df['signup_time'])
        purchase_dt = pd.to_datetime(df['purchase_time'])
        out['hours_since_creation'] = (purchase_dt - signup_dt).dt.total_seconds() / 3600.0
        out['scan_velocity'] = df['device_id'].map(self.device_counts).fillna(1.0)
        
        dev_ip_cnt = df['device_id'].map(self.device_ips).fillna(1.0)
        ip_dev_cnt = df['ip_address'].map(self.ip_devices).fillna(1.0)
        out['is_location_anomaly'] = ((dev_ip_cnt > 1) | (ip_dev_cnt > 1)).astype(int)
        return out

def train_production_models():
    print("=" * 70)
    print("STARTING LEAKAGE-FREE PRODUCTION MODEL TRAINING PIPELINE")
    print("=" * 70)
    
    print(f"Loading dataset from: {FRAUD_DATASET_PATH}")
    df = pd.read_csv(FRAUD_DATASET_PATH)
    
    # 1 = Authentic, 0 = Counterfeit (AuthentiQ standard label convention)
    df['label'] = 1 - df['class']
    
    # Strict Group Split by device_id to ensure 0 data leakage
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_idx, test_idx = next(gss.split(df, df['label'], groups=df['device_id']))
    
    train_df = df.iloc[train_idx].copy()
    test_df = df.iloc[test_idx].copy()
    
    overlap = len(set(train_df['device_id']).intersection(set(test_df['device_id'])))
    print(f"[*] Train Samples: {len(train_df):,} | Test Samples: {len(test_df):,}")
    print(f"[*] Device Overlap: {overlap} (Strictly 0% guaranteed)")
    
    # Fit feature pipeline strictly on train_df
    pipe = LeakageFreePipeline()
    pipe.fit(train_df)
    
    X_train = pipe.transform(train_df)[['scan_velocity', 'hours_since_creation', 'is_location_anomaly']]
    y_train = train_df['label']
    
    X_test = pipe.transform(test_df)[['scan_velocity', 'hours_since_creation', 'is_location_anomaly']]
    y_test = test_df['label']
    
    print("Training Balanced Random Forest Classifier...")
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=5,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)
    
    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"\n[OK] Random Forest Holdout Accuracy (Zero Leakage): {acc * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, preds, target_names=["Counterfeit (0)", "Authentic (1)"], digits=4))
    
    os.makedirs(BACKEND_MODEL_DIR, exist_ok=True)
    model_filename = "rf_model.joblib"
    joblib.dump(clf, model_filename)
    backend_model_path = os.path.join(BACKEND_MODEL_DIR, model_filename)
    shutil.copy(model_filename, backend_model_path)
    print(f"[*] Saved Random Forest model to: {backend_model_path}")
    
    # GNN Model
    if TORCH_AVAILABLE:
        print("\n" + "=" * 70)
        print("TRAINING GNN NETWORK DETECTION MODEL")
        print("=" * 70)
        
        class GNNAuthenticityDetector(nn.Module):
            def __init__(self, in_features=3, hidden_dim=32):
                super(GNNAuthenticityDetector, self).__init__()
                self.conv1 = GCNConv(in_features, hidden_dim)
                self.conv2 = GCNConv(hidden_dim, hidden_dim)
                self.fc = nn.Linear(hidden_dim, 2)

            def forward(self, x, edge_index):
                x = self.conv1(x, edge_index)
                x = F.relu(x)
                x = F.dropout(x, p=0.5, training=self.training)
                x = self.conv2(x, edge_index)
                x = F.relu(x)
                x = self.fc(x)
                return F.log_softmax(x, dim=1)

        num_nodes = 5000
        df_subset = train_df.sample(n=num_nodes, random_state=42).reset_index(drop=True)
        X_sub = pipe.transform(df_subset)[['scan_velocity', 'hours_since_creation', 'is_location_anomaly']].values
        x = torch.tensor(X_sub, dtype=torch.float32)
        y = torch.tensor(df_subset['label'].values, dtype=torch.long)
        
        edges = []
        vel = X_sub[:, 0]
        is_anom = X_sub[:, 2]
        for i in range(num_nodes):
            candidates = np.random.choice(num_nodes, size=20, replace=False)
            for j in candidates:
                if i != j:
                    if (vel[i] == vel[j] and vel[i] > 1) or (is_anom[i] == 1 and is_anom[j] == 1):
                        edges.append([i, j])
                        edges.append([j, i])
                        
        edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous() if len(edges) > 0 else torch.zeros((2, 0), dtype=torch.long)
        
        data = Data(x=x, edge_index=edge_index, y=y)
        model = GNNAuthenticityDetector()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
        criterion = nn.NLLLoss()
        
        model.train()
        for epoch in range(1, 101):
            optimizer.zero_grad()
            out = model(data.x, data.edge_index)
            loss = criterion(out, data.y)
            loss.backward()
            optimizer.step()
            
        gnn_path = os.path.join(BACKEND_MODEL_DIR, "gnn_model.pt")
        torch.save(model.state_dict(), gnn_path)
        print(f"[*] Saved GNN model to: {gnn_path}")

    print("\n" + "=" * 70)
    print("[OK] ALL PRODUCTION MODELS TRAINED & SAVED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    train_production_models()
