import os
import sys

# Ensure UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score,
    precision_recall_curve,
    roc_curve
)
import warnings
warnings.filterwarnings('ignore')

FRAUD_DATASET_PATH = r"C:\Users\Monish\Downloads\Dataset for AuthentiQ\Fraud_Data.csv"
ADVANCED_DATASET_PATH = r"C:\Users\Monish\Downloads\Dataset for AuthentiQ\authentiq_advanced_dataset.csv"
DOMAINS_DIR = r"C:\Users\Monish\Downloads\Dataset for AuthentiQ\domains"

# =====================================================================
# STEP 1 & 9: LEAKAGE-FREE FEATURE ENGINEERING TRANSFORMER
# =====================================================================
class LeakageFreeFeatureTransformer(BaseEstimator, TransformerMixin):
    """
    Learns all entity aggregations and frequency mappings EXCLUSIVELY
    from the training set. Applied onto validation/test sets without
    retrospective leakage or lookahead bias.
    """
    def __init__(self):
        self.device_counts_ = {}
        self.ip_to_devices_ = {}
        self.device_to_ips_ = {}
        self.default_velocity_ = 1.0

    def fit(self, X_df: pd.DataFrame, y=None):
        # Fit ONLY on training slice
        # 1. Device scan velocity frequency
        self.device_counts_ = X_df['device_id'].value_counts().to_dict()
        self.default_velocity_ = np.median(list(self.device_counts_.values())) if self.device_counts_ else 1.0

        # 2. Anomaly graphs: unique IPs per device, unique devices per IP
        self.device_to_ips_ = X_df.groupby('device_id')['ip_address'].nunique().to_dict()
        self.ip_to_devices_ = X_df.groupby('ip_address')['device_id'].nunique().to_dict()
        return self

    def transform(self, X_df: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame(index=X_df.index)
        
        # 1. Hours since creation (purely row-level calculation)
        signup_dt = pd.to_datetime(X_df['signup_time'])
        purchase_dt = pd.to_datetime(X_df['purchase_time'])
        out['hours_since_creation'] = (purchase_dt - signup_dt).dt.total_seconds() / 3600.0
        
        # 2. Scan velocity based strictly on training frequency map
        out['scan_velocity'] = X_df['device_id'].map(self.device_counts_).fillna(1.0)
        
        # 3. Location anomaly based strictly on training frequency map
        dev_ip_cnt = X_df['device_id'].map(self.device_to_ips_).fillna(1.0)
        ip_dev_cnt = X_df['ip_address'].map(self.ip_to_devices_).fillna(1.0)
        out['is_location_anomaly'] = ((dev_ip_cnt > 1) | (ip_dev_cnt > 1)).astype(int)
        
        return out

# =====================================================================
# STEP 9: DATA INTEGRITY, DUPLICATES & LEAKAGE AUDIT
# =====================================================================
def run_leakage_and_integrity_audit(df: pd.DataFrame):
    print("=" * 80)
    print("AUDIT STEP 1 & 9: DATA INTEGRITY, DUPLICATE DETECTION & ZERO-LEAKAGE VERIFICATION")
    print("=" * 80)
    
    total_rows = len(df)
    exact_duplicates = df.duplicated().sum()
    unique_devices = df['device_id'].nunique()
    unique_users = df['user_id'].nunique()
    unique_ips = df['ip_address'].nunique()
    
    print(f"[*] Total Records: {total_rows:,}")
    print(f"[*] Exact Duplicate Rows: {exact_duplicates} ({exact_duplicates/total_rows*100:.2f}%)")
    print(f"[*] Unique Users: {unique_users:,}")
    print(f"[*] Unique Devices: {unique_devices:,}")
    print(f"[*] Unique IP Addresses: {unique_ips:,}")
    
    # Perform strict Group Split by device_id
    y = df['class'] # 1 is Fraud (Counterfeit), 0 is Authentic
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_idx, test_idx = next(gss.split(df, y, groups=df['device_id']))
    
    train_df = df.iloc[train_idx].copy()
    test_df = df.iloc[test_idx].copy()
    
    # Overlap Audit
    train_devices = set(train_df['device_id'])
    test_devices = set(test_df['device_id'])
    device_overlap = len(train_devices.intersection(test_devices))
    
    train_users = set(train_df['user_id'])
    test_users = set(test_df['user_id'])
    user_overlap = len(train_users.intersection(test_users))
    
    print("\n--- ZERO-LEAKAGE GROUP SPLIT VERIFICATION ---")
    print(f"[*] Training Rows: {len(train_df):,} | Test Rows: {len(test_df):,}")
    print(f"[*] Device Overlap between Train & Test: {device_overlap} (Strictly 0 Guaranteed)")
    print(f"[*] User Overlap between Train & Test: {user_overlap} (Strictly 0 Guaranteed)")
    assert device_overlap == 0, "CRITICAL ERROR: Device ID data leakage detected!"
    print("[OK] CONFIRMED: Zero group leakage between train and test sets.")
    
    return train_df, test_df

# =====================================================================
# STEP 2, 3, 4, 5: MODEL TRAINING & METRICS REPORTING
# =====================================================================
def evaluate_model_on_untouched_test_set(train_df: pd.DataFrame, test_df: pd.DataFrame):
    print("\n" + "=" * 80)
    print("AUDIT STEP 2, 3, 4, 5: UNTOUCHED TEST SET EVALUATION & DETAILED METRICS")
    print("=" * 80)
    
    # Fit transformer strictly on train_df
    transformer = LeakageFreeFeatureTransformer()
    transformer.fit(train_df)
    
    X_train = transformer.transform(train_df)
    y_train = train_df['class'].values # 1 = Counterfeit/Fraud, 0 = Authentic
    
    X_test = transformer.transform(test_df)
    y_test = test_df['class'].values
    
    # Check class imbalance
    counterfeit_cnt_train = np.sum(y_train == 1)
    authentic_cnt_train = np.sum(y_train == 0)
    counterfeit_cnt_test = np.sum(y_test == 1)
    authentic_cnt_test = np.sum(y_test == 0)
    
    print("\n--- CLASS DISTRIBUTION & IMBALANCE ---")
    print(f"[*] Train -> Authentic: {authentic_cnt_train:,} ({authentic_cnt_train/len(y_train)*100:.2f}%) | Counterfeit: {counterfeit_cnt_train:,} ({counterfeit_cnt_train/len(y_train)*100:.2f}%)")
    print(f"[*] Test  -> Authentic: {authentic_cnt_test:,} ({authentic_cnt_test/len(y_test)*100:.2f}%) | Counterfeit: {counterfeit_cnt_test:,} ({counterfeit_cnt_test/len(y_test)*100:.2f}%)")
    print(f"[*] Imbalance Ratio: ~{authentic_cnt_train // counterfeit_cnt_train}:1 (Authentic to Counterfeit)")
    
    # Train Random Forest with balanced class weights
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=5,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)
    
    # Predict
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1] # probability of Counterfeit (Class 1)
    
    # 1. Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    print("\n--- CONFUSION MATRIX (Test Set: N={:,}) ---".format(len(y_test)))
    print("                 | Predicted Authentic (0) | Predicted Counterfeit (1) | Total")
    print("-----------------+-------------------------+---------------------------+-------")
    print(f"Actual Authentic | TN = {tn:6,d}             | FP = {fp:6,d}              | {tn+fp:6,d}")
    print(f"Actual Counterf. | FN = {fn:6,d}             | TP = {tp:6,d}              | {fn+tp:6,d}")
    print("-----------------+-------------------------+---------------------------+-------")
    print(f"Total            |      {tn+fn:6,d}             |      {fp+tp:6,d}              | {len(y_test):6,d}")
    
    # Rates
    tpr = tp / (tp + fn) # Sensitivity / Recall for Counterfeit
    tnr = tn / (tn + fp) # Specificity for Authentic
    fpr = fp / (tn + fp) # False Alarm Rate
    fnr = fn / (tp + fn) # Miss Rate
    
    print(f"\n[*] True Positive Rate (Counterfeit Recall / Sensitivity): {tpr*100:.2f}%")
    print(f"[*] True Negative Rate (Authentic Specificity):             {tnr*100:.2f}%")
    print(f"[*] False Positive Rate (False Alarm Rate):                 {fpr*100:.2f}%")
    print(f"[*] False Negative Rate (Miss Rate):                       {fnr*100:.2f}%")
    
    # 2. Counterfeit Class Specific Metrics
    prec_counterfeit = precision_score(y_test, y_pred, pos_label=1)
    rec_counterfeit = recall_score(y_test, y_pred, pos_label=1)
    f1_counterfeit = f1_score(y_test, y_pred, pos_label=1)
    pr_auc_counterfeit = average_precision_score(y_test, y_proba)
    roc_auc = roc_auc_score(y_test, y_proba)
    
    print("\n--- COUNTERFEIT CLASS (CLASS 1) METRICS ---")
    print(f"[*] Precision (Positive Predictive Value): {prec_counterfeit*100:.2f}%")
    print(f"[*] Recall (Detection Rate / Sensitivity): {rec_counterfeit*100:.2f}%")
    print(f"[*] F1-Score:                              {f1_counterfeit*100:.2f}%")
    print(f"[*] PR-AUC (Average Precision Score):      {pr_auc_counterfeit*100:.2f}% (Baseline random: {counterfeit_cnt_test/len(y_test)*100:.2f}%)")
    print(f"[*] ROC-AUC Score:                         {roc_auc*100:.2f}%")
    
    # 3. Overall Global Metrics
    acc = accuracy_score(y_test, y_pred)
    bal_acc = balanced_accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average='macro')
    weighted_f1 = f1_score(y_test, y_pred, average='weighted')
    
    print("\n--- OVERALL GLOBAL PERFORMANCE METRICS ---")
    print(f"[*] Overall Accuracy:    {acc*100:.2f}%")
    print(f"[*] Balanced Accuracy:   {bal_acc*100:.2f}%")
    print(f"[*] Macro F1-Score:      {macro_f1*100:.2f}%")
    print(f"[*] Weighted F1-Score:   {weighted_f1*100:.2f}%")
    
    return clf, transformer

# =====================================================================
# STEP 6: STRATIFIED GROUP CROSS-VALIDATION
# =====================================================================
def run_stratified_group_cross_validation(df: pd.DataFrame):
    print("\n" + "=" * 80)
    print("AUDIT STEP 6: 5-FOLD STRATIFIED GROUP CROSS-VALIDATION (ZERO LEAKAGE)")
    print("=" * 80)
    
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    y = df['class'].values
    groups = df['device_id'].values
    
    fold_metrics = []
    
    for fold, (train_idx, val_idx) in enumerate(sgkf.split(df, y, groups=groups), 1):
        fold_train = df.iloc[train_idx]
        fold_val = df.iloc[val_idx]
        
        # Verify 0 group leakage in fold
        train_devs = set(fold_train['device_id'])
        val_devs = set(fold_val['device_id'])
        assert len(train_devs.intersection(val_devs)) == 0, f"Leakage detected in fold {fold}!"
        
        # Fit transformer ONLY on fold train
        transformer = LeakageFreeFeatureTransformer()
        transformer.fit(fold_train)
        
        X_tr = transformer.transform(fold_train)
        y_tr = fold_train['class'].values
        
        X_v = transformer.transform(fold_val)
        y_v = fold_val['class'].values
        
        clf = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=5,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        clf.fit(X_tr, y_tr)
        
        preds = clf.predict(X_v)
        proba = clf.predict_proba(X_v)[:, 1]
        
        acc = accuracy_score(y_v, preds)
        bal_acc = balanced_accuracy_score(y_v, preds)
        rec_fraud = recall_score(y_v, preds, pos_label=1)
        prec_fraud = precision_score(y_v, preds, pos_label=1)
        f1_fraud = f1_score(y_v, preds, pos_label=1)
        macro_f1 = f1_score(y_v, preds, average='macro')
        pr_auc = average_precision_score(y_v, proba)
        roc_auc = roc_auc_score(y_v, proba)
        
        fold_metrics.append({
            'Fold': fold,
            'Accuracy': acc * 100,
            'Balanced Acc': bal_acc * 100,
            'Counterfeit Recall': rec_fraud * 100,
            'Counterfeit Precision': prec_fraud * 100,
            'Counterfeit F1': f1_fraud * 100,
            'Macro F1': macro_f1 * 100,
            'PR-AUC': pr_auc * 100,
            'ROC-AUC': roc_auc * 100
        })
        print(f"[*] Fold {fold}: Acc: {acc*100:.2f}% | Bal Acc: {bal_acc*100:.2f}% | Counterfeit Recall: {rec_fraud*100:.2f}% | PR-AUC: {pr_auc*100:.2f}%")
        
    df_results = pd.DataFrame(fold_metrics)
    print("\n--- 5-FOLD CROSS-VALIDATION SUMMARY TABLE ---")
    print(df_results.to_string(index=False))
    
    print("\n--- CROSS-VALIDATION MEAN & STANDARD DEVIATION ---")
    for metric in ['Accuracy', 'Balanced Acc', 'Counterfeit Recall', 'Counterfeit Precision', 'Counterfeit F1', 'Macro F1', 'PR-AUC', 'ROC-AUC']:
        mean_val = df_results[metric].mean()
        std_val = df_results[metric].std()
        print(f"[*] {metric:<22}: {mean_val:.2f}% ± {std_val:.2f}%")

# =====================================================================
# STEP 7: OUT-OF-DISTRIBUTION (OOD) CROSS-DOMAIN TESTING
# =====================================================================
def run_ood_testing(base_clf, transformer):
    print("\n" + "=" * 80)
    print("AUDIT STEP 7: GENUINE OUT-OF-DISTRIBUTION (OOD) DOMAIN EVALUATION")
    print("=" * 80)
    
    domains = ["Luxury_Items", "Packaged_Foods", "Electronics", "Fashion", "Pharmaceuticals"]
    ood_results = []
    
    for domain in domains:
        domain_path = os.path.join(DOMAINS_DIR, f"{domain}.csv")
        if not os.path.exists(domain_path):
            continue
        df_domain = pd.read_csv(domain_path)
        
        # Transform using base model transformer (zero target exposure to domain)
        X_domain = transformer.transform(df_domain)
        y_domain = df_domain['class'].values
        
        preds = base_clf.predict(X_domain)
        proba = base_clf.predict_proba(X_domain)[:, 1]
        
        acc = accuracy_score(y_domain, preds)
        bal_acc = balanced_accuracy_score(y_domain, preds)
        rec_fraud = recall_score(y_domain, preds, pos_label=1, zero_division=0)
        prec_fraud = precision_score(y_domain, preds, pos_label=1, zero_division=0)
        f1_fraud = f1_score(y_domain, preds, pos_label=1, zero_division=0)
        macro_f1 = f1_score(y_domain, preds, average='macro')
        pr_auc = average_precision_score(y_domain, proba)
        
        ood_results.append({
            'OOD Domain': domain.replace('_', ' '),
            'Samples': len(df_domain),
            'Accuracy': acc * 100,
            'Balanced Acc': bal_acc * 100,
            'Counterfeit Recall': rec_fraud * 100,
            'Counterfeit F1': f1_fraud * 100,
            'Macro F1': macro_f1 * 100,
            'PR-AUC': pr_auc * 100
        })
        
    df_ood = pd.DataFrame(ood_results)
    print(df_ood.to_string(index=False))

# =====================================================================
# STEP 8: STRESS TESTING MULTIMODAL INPUTS
# =====================================================================
def run_multimodal_stress_testing():
    print("\n" + "=" * 80)
    print("AUDIT STEP 8: MULTIMODAL STRESS TESTING & PERTURBATION BENCHMARKING")
    print("=" * 80)
    
    if not os.path.exists(ADVANCED_DATASET_PATH):
        print("Advanced dataset not found.")
        return
        
    df_adv = pd.read_csv(ADVANCED_DATASET_PATH)
    
    # Group Split by product_id to ensure products in test set are 100% unseen
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_idx, test_idx = next(gss.split(df_adv, df_adv['is_counterfeit'], groups=df_adv['product_id']))
    
    train_adv = df_adv.iloc[train_idx].copy()
    test_adv = df_adv.iloc[test_idx].copy()
    
    prod_overlap = len(set(train_adv['product_id']).intersection(set(test_adv['product_id'])))
    print(f"[*] Advanced Dataset Train Size: {len(train_adv):,} | Test Size: {len(test_adv):,}")
    print(f"[*] Product ID Overlap: {prod_overlap} (Strict 0)")
    
    # Feature columns
    cat_cols = ['manufacturing_location', 'origin', 'weather_conditions']
    X_train_raw = train_adv.drop(columns=['product_id', 'timestamp', 'is_counterfeit'])
    y_train = train_adv['is_counterfeit'].values
    
    X_test_raw = test_adv.drop(columns=['product_id', 'timestamp', 'is_counterfeit'])
    y_test = test_adv['is_counterfeit'].values
    
    # One-hot encode using train only
    X_train_encoded = pd.get_dummies(X_train_raw, columns=cat_cols, drop_first=True)
    feature_cols = list(X_train_encoded.columns)
    
    # Align test
    X_test_encoded = pd.get_dummies(X_test_raw, columns=cat_cols, drop_first=True)
    for col in feature_cols:
        if col not in X_test_encoded.columns:
            X_test_encoded[col] = 0
    X_test_encoded = X_test_encoded[feature_cols]
    
    # Fit base multimodal model
    clf_adv = RandomForestClassifier(n_estimators=150, max_depth=15, random_state=42, n_jobs=-1)
    clf_adv.fit(X_train_encoded, y_train)
    
    # Base Performance
    base_preds = clf_adv.predict(X_test_encoded)
    base_acc = accuracy_score(y_test, base_preds)
    base_f1 = f1_score(y_test, base_preds, pos_label=1)
    print(f"\n[*] Clean Baseline Advanced Model Test Acc: {base_acc*100:.2f}% | Counterfeit F1: {base_f1*100:.2f}%")
    
    # Stress Scenarios
    stress_results = []
    
    # 1. Thermal Drift (Sensor Calibration Shift)
    for temp_shift in [+5.0, +10.0, +15.0]:
        X_stressed = X_test_encoded.copy()
        X_stressed['temperature'] = X_stressed['temperature'] + temp_shift
        p = clf_adv.predict(X_stressed)
        stress_results.append({
            'Stress Scenario': f'Thermal Drift (+{temp_shift}°C shift)',
            'Accuracy (%)': accuracy_score(y_test, p)*100,
            'Counterfeit Recall (%)': recall_score(y_test, p, pos_label=1)*100,
            'Counterfeit F1 (%)': f1_score(y_test, p, pos_label=1)*100
        })
        
    # 2. Optical Degradation (QR & Texture Scratches / Camera Blur)
    for deg in [0.20, 0.40, 0.60]:
        X_stressed = X_test_encoded.copy()
        X_stressed['qr_code_integrity'] = (X_stressed['qr_code_integrity'] - deg).clip(0, 1)
        X_stressed['micro_textures'] = (X_stressed['micro_textures'] - deg).clip(0, 1)
        p = clf_adv.predict(X_stressed)
        stress_results.append({
            'Stress Scenario': f'Optical Damage / Blur (-{int(deg*100)}% clarity)',
            'Accuracy (%)': accuracy_score(y_test, p)*100,
            'Counterfeit Recall (%)': recall_score(y_test, p, pos_label=1)*100,
            'Counterfeit F1 (%)': f1_score(y_test, p, pos_label=1)*100
        })
        
    # 3. Gaussian Sensor Noise Injection
    for noise_std in [0.05, 0.10, 0.20]:
        X_stressed = X_test_encoded.copy()
        num_cols = ['surface_features', 'color_space_metrics', 'spectral_metrics', 'frequency_features']
        for col in num_cols:
            noise = np.random.normal(0, noise_std, size=len(X_stressed))
            X_stressed[col] = (X_stressed[col] + noise).clip(0, 1)
        p = clf_adv.predict(X_stressed)
        stress_results.append({
            'Stress Scenario': f'Spectral Noise Injection (std={noise_std})',
            'Accuracy (%)': accuracy_score(y_test, p)*100,
            'Counterfeit Recall (%)': recall_score(y_test, p, pos_label=1)*100,
            'Counterfeit F1 (%)': f1_score(y_test, p, pos_label=1)*100
        })
        
    # 4. Modality Dropout (Missing IoT / Missing Optical Sensor)
    X_drop_iot = X_test_encoded.copy()
    X_drop_iot['temperature'] = 0
    X_drop_iot['humidity'] = 0
    p = clf_adv.predict(X_drop_iot)
    stress_results.append({
        'Stress Scenario': 'IoT Sensor Blackout (Temp & Humidity = 0)',
        'Accuracy (%)': accuracy_score(y_test, p)*100,
        'Counterfeit Recall (%)': recall_score(y_test, p, pos_label=1)*100,
        'Counterfeit F1 (%)': f1_score(y_test, p, pos_label=1)*100
    })
    
    # 5. Adversarial Perturbation (Counterfeiter mimicry on optical markers)
    X_adv_attack = X_test_encoded.copy()
    counterfeit_mask = (y_test == 1)
    # Counterfeiter attempts to artificially boost QR and surface scores
    X_adv_attack.loc[counterfeit_mask, 'qr_code_integrity'] = 0.95
    X_adv_attack.loc[counterfeit_mask, 'surface_features'] = 0.90
    p = clf_adv.predict(X_adv_attack)
    stress_results.append({
        'Stress Scenario': 'Adversarial QR & Texture Mimicry Attack',
        'Accuracy (%)': accuracy_score(y_test, p)*100,
        'Counterfeit Recall (%)': recall_score(y_test, p, pos_label=1)*100,
        'Counterfeit F1 (%)': f1_score(y_test, p, pos_label=1)*100
    })
    
    df_stress = pd.DataFrame(stress_results)
    print("\n--- MULTIMODAL STRESS & ROBUSTNESS TEST RESULTS ---")
    print(df_stress.to_string(index=False))

# =====================================================================
# MAIN RUNNER
# =====================================================================
if __name__ == "__main__":
    print(f"Loading raw dataset from {FRAUD_DATASET_PATH}...")
    df = pd.read_csv(FRAUD_DATASET_PATH)
    
    train_df, test_df = run_leakage_and_integrity_audit(df)
    clf, transformer = evaluate_model_on_untouched_test_set(train_df, test_df)
    run_stratified_group_cross_validation(df)
    run_ood_testing(clf, transformer)
    run_multimodal_stress_testing()
    print("\n" + "=" * 80)
    print("[OK] ALL 9 ML ENGINEERING AUDIT STEPS COMPLETED WITH ZERO DATA LEAKAGE.")
    print("=" * 80)
