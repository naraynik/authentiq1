import os
import logging
import joblib
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)

TORCH_AVAILABLE = False
try:
    import torch
    import torch.nn.functional as F
    import torch.nn as nn
    from torch_geometric.nn import GCNConv
    TORCH_AVAILABLE = True
except Exception as e:
    logger.warning(f"Torch/GNN support disabled: {e}")
    torch = None
    F = None
    nn = None
    GCNConv = None

if TORCH_AVAILABLE:
    class GNNAuthenticityDetector(nn.Module):
        """Graph Neural Network for detecting counterfeiting networks."""
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
else:
    class GNNAuthenticityDetector:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("GNN model unavailable because torch/torch-geometric is not installed")

class AIClient:
    def __init__(self):
        self.rf_model = None
        self.gnn_model = None
        self.rf_model_path = settings.RF_MODEL_PATH
        self.gnn_model_path = settings.GNN_MODEL_PATH
        self.device = torch.device('cpu') if TORCH_AVAILABLE else None
        self.load_models()

    def load_models(self):
        """Load both Random Forest and GNN models."""
        if os.path.exists(self.rf_model_path):
            try:
                self.rf_model = joblib.load(self.rf_model_path)
                logger.info(f"✓ Random Forest model loaded from {self.rf_model_path}")
            except Exception as e:
                logger.error(f"Error loading RF model: {e}")
        else:
            logger.warning(f"Random Forest model not found at {self.rf_model_path}")

        if TORCH_AVAILABLE and os.path.exists(self.gnn_model_path):
            try:
                state = torch.load(self.gnn_model_path, map_location=self.device)
                # Determine input feature dimension dynamically from state dict
                if 'conv1.lin.weight' in state:
                    in_feat = state['conv1.lin.weight'].shape[1]
                else:
                    in_feat = 3
                
                # Check architecture: 2-layer GNN or GNN with linear head
                if 'fc.weight' in state:
                    class DynamicGNN(nn.Module):
                        def __init__(self, in_c, hid_c=32):
                            super().__init__()
                            self.conv1 = GCNConv(in_c, hid_c)
                            self.conv2 = GCNConv(hid_c, hid_c)
                            self.fc = nn.Linear(hid_c, 2)
                        def forward(self, x, edge_index):
                            x = F.relu(self.conv1(x, edge_index))
                            x = F.dropout(x, p=0.5, training=self.training)
                            x = F.relu(self.conv2(x, edge_index))
                            return F.log_softmax(self.fc(x), dim=1)
                    self.gnn_model = DynamicGNN(in_feat, 32).to(self.device)
                else:
                    class DynamicGNN(nn.Module):
                        def __init__(self, in_c, hid_c=32):
                            super().__init__()
                            self.conv1 = GCNConv(in_c, hid_c)
                            self.conv2 = GCNConv(hid_c, 2)
                        def forward(self, x, edge_index):
                            x = F.relu(self.conv1(x, edge_index))
                            x = F.dropout(x, p=0.5, training=self.training)
                            x = self.conv2(x, edge_index)
                            return F.log_softmax(x, dim=1)
                    self.gnn_model = DynamicGNN(in_feat, 32).to(self.device)
                    
                self.gnn_model.load_state_dict(state)
                self.gnn_model.eval()
                logger.info(f"✓ GNN model loaded from {self.gnn_model_path} (in_features={in_feat})")
            except Exception as e:
                logger.error(f"Error loading GNN model: {e}")
        elif not TORCH_AVAILABLE:
            logger.info("GNN model disabled because torch/torch-geometric is unavailable")
        else:
            logger.warning(f"GNN model not found at {self.gnn_model_path}")

    def evaluate_scan_advanced(self, verify_data: dict) -> dict:
        flags = []
        if verify_data.get('qr_code_integrity', 1.0) < 0.8:
            flags.append("Degraded QR Code Integrity")
        if verify_data.get('micro_textures', 1.0) < 0.7:
            flags.append("Abnormal Micro-textures")
        if verify_data.get('temperature', 22) > 26:
            flags.append("Temperature Out of Bounds")
            
        rf_scores = None
        authenticity_prob = 0.5
        anomaly_score = 0.5
        
        if self.rf_model and isinstance(self.rf_model, dict) and 'model' in self.rf_model:
            try:
                import pandas as pd
                df = pd.DataFrame([verify_data])
                if 'manufacturing_location' in df.columns:
                    df = pd.get_dummies(df, columns=['manufacturing_location', 'origin', 'weather_conditions'], drop_first=True)
                
                clf = self.rf_model['model']
                features_list = self.rf_model['features']
                
                for col in features_list:
                    if col not in df.columns:
                        df[col] = 0
                X = df[features_list].astype(float)
                
                probs = clf.predict_proba(X)[0]
                authenticity_prob = float(probs[0]) # class 0 is authentic
                anomaly_score = float(probs[1])     # class 1 is counterfeit
                
                rf_scores = {
                    'authenticity_prob': authenticity_prob,
                    'counterfeit_prob': anomaly_score
                }
            except Exception as e:
                logger.error(f"Error in Advanced RF prediction: {e}")
        
        if anomaly_score > 0.6 or len(flags) >= 2:
            final_verdict = "counterfeit"
        elif anomaly_score < 0.4 and len(flags) == 0:
            final_verdict = "authentic"
        else:
            final_verdict = "suspicious"

        return {
            'authenticity_probability': authenticity_prob,
            'anomaly_score': anomaly_score,
            'flags': flags,
            'final_verdict': final_verdict,
            'model_scores': {
                'random_forest': rf_scores
            }
        }

    @staticmethod
    def _scan_feature_row(scan_velocity: int, hours_since_creation: float, is_location_anomaly: int) -> dict:
        """Map scan behaviour onto the advanced models' optical/IoT feature space."""
        return {
            'hours_since_creation': hours_since_creation,
            'scan_velocity': scan_velocity,
            'is_location_anomaly': is_location_anomaly,
            'temperature': 22.0,
            'humidity': 45.0,
            'micro_textures': 0.95 if is_location_anomaly == 0 else 0.50,
            'color_printing_patterns': 0.92,
            'geometric_alignment': 0.98,
            'surface_features': 0.90,
            'printing_artifacts': 0.96,
            'frequency_features': 0.85,
            'color_space_metrics': 0.94,
            'spectral_metrics': 0.91,
            'deep_learning_latent_features': 0.88,
            'qr_code_integrity': 0.99 if scan_velocity <= 3 else 0.60,
            'barcode_integrity': 0.99
        }

    def evaluate_scan_graph(self, scans: list) -> dict:
        """GNN over one product's scan history.

        `scans` is a list of (scan_velocity, hours_since_creation, is_location_anomaly),
        oldest first, the current scan last. Nodes are scans, edges link consecutive
        scans of the same code (the same idea as training, where products from the same
        origin were linked). Returns the counterfeit probability of the current scan,
        or None when the GNN is unavailable.
        """
        if not self.gnn_model or not TORCH_AVAILABLE or not scans:
            return None
        if not (isinstance(self.rf_model, dict) and 'features' in self.rf_model):
            return None
        try:
            features = self.rf_model['features']
            if self.gnn_model.conv1.lin.weight.shape[1] != len(features):
                return None
            rows = [self._scan_feature_row(v, h, a) for v, h, a in scans]
            x = torch.tensor([[float(r.get(f, 0.0)) for f in features] for r in rows], dtype=torch.float32)
            n = len(rows)
            pairs = [[i, i + 1] for i in range(n - 1)] + [[i + 1, i] for i in range(n - 1)]
            edge_index = (torch.tensor(pairs, dtype=torch.long).T if pairs
                          else torch.zeros((2, 0), dtype=torch.long))
            with torch.no_grad():
                probs = torch.exp(self.gnn_model(x.to(self.device), edge_index.to(self.device)))
            # Advanced models: class 1 = counterfeit
            return {
                'counterfeit_prob': float(probs[-1, 1].item()),
                'nodes': n,
            }
        except Exception as e:
            logger.error(f"Error in GNN scan-graph prediction: {e}")
            return None

    def evaluate_with_random_forest(self, scan_velocity: int, hours_since_creation: float, is_location_anomaly: int) -> dict:
        """Random Forest prediction for individual product authenticity."""
        if not self.rf_model:
            return None
        try:
            clf = self.rf_model['model'] if isinstance(self.rf_model, dict) else self.rf_model
            # If advanced model expecting more columns, construct aligned defaults
            if isinstance(self.rf_model, dict) and 'features' in self.rf_model:
                features_list = self.rf_model['features']
                import pandas as pd
                row = self._scan_feature_row(scan_velocity, hours_since_creation, is_location_anomaly)
                df = pd.DataFrame([row])
                for col in features_list:
                    if col not in df.columns:
                        df[col] = 0
                probs = clf.predict_proba(df[features_list].astype(float))[0]
                # Label in advanced model: class 0 is authentic, class 1 is counterfeit
                return {
                    'authenticity_prob': float(probs[0]),
                    'counterfeit_prob': float(probs[1])
                }
            else:
                features = np.array([[scan_velocity, hours_since_creation, is_location_anomaly]])
                probs = clf.predict_proba(features)[0]
                return {
                    'authenticity_prob': float(probs[1]),
                    'counterfeit_prob': float(probs[0])
                }
        except Exception as e:
            logger.error(f"Error in RF prediction: {e}")
            return None

    def evaluate_with_gnn(self, product_vectors: np.ndarray, edge_connections: list) -> dict:
        """GNN network-level prediction."""
        if not self.gnn_model or not TORCH_AVAILABLE:
            return None
        try:
            x = torch.tensor(product_vectors, dtype=torch.float32).to(self.device)
            if len(edge_connections) > 0:
                edge_index = torch.tensor(edge_connections, dtype=torch.long).T.to(self.device)
            else:
                edge_index = torch.zeros((2, 0), dtype=torch.long).to(self.device)
            with torch.no_grad():
                logits = self.gnn_model(x, edge_index)
                probs = torch.softmax(logits, dim=1)
            return {
                'network_scores': probs[:, 1].cpu().numpy(),
                'mean_authenticity': float(probs[:, 1].mean().item()),
                'mean_counterfeit_risk': float(probs[:, 0].mean().item())
            }
        except Exception as e:
            logger.error(f"Error in GNN prediction: {e}")
            return None

    def evaluate_scan(self, scan_velocity: int, hours_since_creation: float, location: str,
                     product_network: dict = None) -> dict:
        """Combined evaluation using both Random Forest and optional GNN."""
        is_location_anomaly = 1 if any(x in location.lower() for x in ["tokyo", "japan", "suspicious"]) else 0
        flags = []
        if scan_velocity > 5:
            flags.append("High Scan Frequency")
        if is_location_anomaly:
            flags.append("Geographical Velocity Violation")
        if hours_since_creation < 0.5:
            flags.append("Pre-mature Scan Sequence")

        rf_result = self.evaluate_with_random_forest(scan_velocity, hours_since_creation, is_location_anomaly)
        gnn_result = None
        if product_network and self.gnn_model:
            gnn_result = self.evaluate_with_gnn(
                product_network.get('product_vectors'),
                product_network.get('edge_connections', [])
            )

        if rf_result and gnn_result:
            combined_authenticity = (0.6 * rf_result['authenticity_prob'] +
                                     0.4 * gnn_result['mean_authenticity'])
            combined_risk = 1.0 - combined_authenticity
            if gnn_result['mean_counterfeit_risk'] > 0.7:
                flags.append("Counterfeiting Network Detected")
        elif rf_result:
            combined_authenticity = rf_result['authenticity_prob']
            combined_risk = rf_result['counterfeit_prob']
        else:
            combined_authenticity = self._heuristic_evaluation(scan_velocity, hours_since_creation, is_location_anomaly)
            combined_risk = 1.0 - combined_authenticity

        return {
            "authenticity_probability": float(combined_authenticity),
            "anomaly_score": float(combined_risk),
            "flags": flags,
            "model_scores": {
                "random_forest": rf_result,
                "gnn_network": gnn_result
            }
        }

    def _heuristic_evaluation(self, scan_velocity: int, hours_since_creation: float, is_location_anomaly: int) -> float:
        """Fallback heuristic evaluation."""
        base_prob = 0.98
        if scan_velocity > 10:
            base_prob -= 0.60
        elif scan_velocity > 3:
            base_prob -= 0.20
        if is_location_anomaly:
            base_prob -= 0.70
        if hours_since_creation < 1.0:
            base_prob -= 0.15
        return max(0.0, min(1.0, base_prob))

ai_client = AIClient()
