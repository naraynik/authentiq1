import pandas as pd
import numpy as np
import os
import shutil
import joblib
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# Try to import torch and torch_geometric for GNN
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch_geometric.data import Data
    from torch_geometric.nn import GCNConv
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("WARNING: torch or torch_geometric not found. GNN model will not be trained.")

# Paths
DATA_FILE = r"C:\Users\Monish\Downloads\Dataset for AuthentiQ\authentiq_advanced_dataset.csv"
BACKEND_MODEL_DIR = os.path.join("..", "backend", "app", "models")

def train_rf(df):
    print("\n" + "="*60)
    print("TRAINING ADVANCED OPTICAL/IOT RANDOM FOREST MODEL")
    print("="*60)
    
    # Drop IDs and target
    X = df.drop(columns=['product_id', 'timestamp', 'is_counterfeit'])
    y = df['is_counterfeit']
    
    # One-hot encode categorical features
    X = pd.get_dummies(X, columns=['manufacturing_location', 'origin', 'weather_conditions'], drop_first=True)
    
    # Save the feature names so the backend can align incoming requests
    feature_names = list(X.columns)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    clf = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, class_weight='balanced', n_jobs=-1)
    clf.fit(X_train, y_train)
    
    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"Random Forest Test Accuracy: {acc*100:.2f}%")
    print(classification_report(y_test, preds))
    
    # Save model and feature columns
    os.makedirs(BACKEND_MODEL_DIR, exist_ok=True)
    model_data = {
        'model': clf,
        'features': feature_names
    }
    rf_path = os.path.join(BACKEND_MODEL_DIR, "rf_advanced_model.joblib")
    joblib.dump(model_data, rf_path)
    print(f"[*] Saved Advanced RF Model to {rf_path}")
    return X, y

def train_gnn(X, y, df):
    if not TORCH_AVAILABLE:
        return
        
    print("\n" + "="*60)
    print("TRAINING GNN SUPPLY CHAIN MODEL")
    print("="*60)
    
    # We will build a graph connecting products from the same origin to detect counterfeit clusters
    print("Building graph...")
    # For speed, we just connect a subset (e.g., first 5000 products)
    subset_size = min(5000, len(df))
    X_sub = X.iloc[:subset_size].values
    y_sub = y.iloc[:subset_size].values
    origin_sub = df['origin'].iloc[:subset_size].values
    
    # Create edges for products sharing the same origin
    # (In a real system, edges could be shared batch IDs or transit routes)
    edges = []
    for i in range(subset_size):
        for j in range(i+1, min(i+50, subset_size)): # limit connections
            if origin_sub[i] == origin_sub[j]:
                edges.append([i, j])
                edges.append([j, i])
                
    if not edges:
        print("No edges found. Skipping GNN.")
        return
        
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    x_tensor = torch.tensor(X_sub, dtype=torch.float)
    y_tensor = torch.tensor(y_sub, dtype=torch.long)
    
    data = Data(x=x_tensor, edge_index=edge_index, y=y_tensor)
    
    class AdvancedGNN(nn.Module):
        def __init__(self, in_channels, hidden_channels):
            super(AdvancedGNN, self).__init__()
            self.conv1 = GCNConv(in_channels, hidden_channels)
            self.conv2 = GCNConv(hidden_channels, 2)

        def forward(self, x, edge_index):
            x = self.conv1(x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, p=0.5, training=self.training)
            x = self.conv2(x, edge_index)
            return F.log_softmax(x, dim=1)
            
    model = AdvancedGNN(x_tensor.size(1), 32)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
    
    model.train()
    for epoch in range(1, 101):
        optimizer.zero_grad()
        out = model(data.x, data.edge_index)
        loss = F.nll_loss(out, data.y)
        loss.backward()
        optimizer.step()
        if epoch % 20 == 0:
            pred = out.argmax(dim=1)
            acc = int((pred == data.y).sum()) / data.y.size(0)
            print(f"Epoch {epoch:03d}, Loss: {loss:.4f}, Train Acc: {acc:.4f}")
            
    model.eval()
    out = model(data.x, data.edge_index)
    pred = out.argmax(dim=1)
    acc = int((pred == data.y).sum()) / data.y.size(0)
    print(f"Final GNN Accuracy on Subset: {acc*100:.2f}%")
    
    gnn_path = os.path.join(BACKEND_MODEL_DIR, "gnn_advanced_model.pt")
    torch.save(model.state_dict(), gnn_path)
    print(f"[*] Saved Advanced GNN Model to {gnn_path}")
    
if __name__ == "__main__":
    print(f"Loading data from {DATA_FILE}")
    df = pd.read_csv(DATA_FILE)
    X, y = train_rf(df)
    train_gnn(X, y, df)
    print("DONE!")
