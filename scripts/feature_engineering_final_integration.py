"""
feature_engineering_final_integration.py
=======================================
Phase 3 Final — Normalization, SMOTE, Final Dataset

Applies:
1. StandardScaler normalization
2. SMOTE class balancing
3. Train/test split
4. Final model-ready datasets

Output:
- tb_multimodal_integrated_final.csv (all samples, normalized, SMOTE-balanced)
- tb_train_set.csv (training data)
- tb_test_set.csv (test data)
- feature_metadata.csv (feature descriptions)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split
import json

# ── Paths ────────────────────────────────────────────────────────────────────
PATIENT_MATRIX = Path("data/processed/tb_multimodal_patient_matrix_raw.csv")
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("Phase 3 Final — Normalization, Balancing & Final Integration")
print("=" * 70)

# ── Step 1: Load patient matrix ───────────────────────────────────────────────

print(f"\n[1] Loading patient matrix...")
df = pd.read_csv(PATIENT_MATRIX)
print(f"    Shape: {df.shape}")
print(f"    Columns: {df.columns.tolist()[:10]}...")

# ── Step 2: Separate metadata, features, labels ──────────────────────────────

print(f"\n[2] Separating metadata / features / labels...")

meta_cols = ["patient_id", "sample_id_full", "city", "year", "label", "label_binary", "dataset", "split", "sample_id"]
meta = df[meta_cols].copy()

# Feature columns (everything except metadata) - exclude ALL non-numeric
feature_cols = [c for c in df.columns if c not in meta_cols]
X = df[feature_cols].copy()

# Drop any remaining non-numeric columns
X = X.select_dtypes(include=[np.number])
feature_cols = X.columns.tolist()

y = df["label_binary"].copy()

print(f"    Metadata columns: {len(meta_cols)}")
print(f"    Feature columns: {len(feature_cols)}")
print(f"    Samples: {X.shape[0]}")
print(f"    Label distribution (before SMOTE):")
print(f"      TB=1: {sum(y)} ({100*sum(y)/len(y):.1f}%)")
print(f"      Ctrl=0: {len(y)-sum(y)} ({100*(len(y)-sum(y))/len(y):.1f}%)")

# ── Step 3: Apply StandardScaler ──────────────────────────────────────────────

print(f"\n[3] Applying StandardScaler normalization...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_scaled = pd.DataFrame(X_scaled, columns=feature_cols, index=X.index)

print(f"    Normalized features (mean ≈ 0, std ≈ 1):")
print(f"      Mean: {X_scaled.mean().mean():.6f}")
print(f"      Std:  {X_scaled.std().mean():.6f}")
# ── Step 3b: Handle remaining NaN values before SMOTE ────────────────────────

print(f"\n[3b] Checking for NaN values...")
nan_counts = X_scaled.isna().sum()
if nan_counts.sum() > 0:
    print(f"    Found {nan_counts.sum()} NaN values; filling with column mean...")
    X_scaled = X_scaled.fillna(X_scaled.mean())
    remaining_nans = X_scaled.isna().sum().sum()
    if remaining_nans > 0:
        print(f"    WARNING: {remaining_nans} NaNs after fill; dropping rows with NaN...")
        valid_rows = ~X_scaled.isna().any(axis=1)
        X_scaled = X_scaled[valid_rows]
        y = y[valid_rows]
        meta = meta[valid_rows]
        print(f"    Samples after NaN removal: {len(y)}")
else:
    print(f"    No NaN values found ✓")
# ── Step 4: Apply SMOTE for class balancing ──────────────────────────────────

print(f"\n[4] Applying SMOTE for class balancing...")
smote = SMOTE(random_state=42, k_neighbors=5)
X_resampled, y_resampled = smote.fit_resample(X_scaled, y)

print(f"    After SMOTE:")
print(f"      Total samples: {len(y_resampled)} (was {len(y)})")
print(f"      TB=1: {sum(y_resampled)} ({100*sum(y_resampled)/len(y_resampled):.1f}%)")
print(f"      Ctrl=0: {len(y_resampled)-sum(y_resampled)} ({100*(len(y_resampled)-sum(y_resampled))/len(y_resampled):.1f}%)")

# Update metadata for synthetic SMOTE samples
n_original = len(y)
n_synthetic = len(y_resampled) - n_original

if n_synthetic > 0:
    # Add synthetic patient IDs
    synthetic_meta = meta.sample(n=n_synthetic, replace=True, random_state=42).reset_index(drop=True)
    synthetic_meta["patient_id"] = [f"SMOTE_{i:04d}" for i in range(n_synthetic)]
    meta_resampled = pd.concat([meta.reset_index(drop=True), synthetic_meta], ignore_index=True)
else:
    meta_resampled = meta.reset_index(drop=True)

# ── Step 5: Create final integrated dataset ──────────────────────────────────

print(f"\n[5] Creating final integrated dataset...")

# Drop the original label columns from metadata (we'll add y_resampled instead)
meta_resampled_clean = meta_resampled.drop(columns=["label", "label_binary"], errors="ignore")

df_final = pd.concat([
    meta_resampled_clean.reset_index(drop=True),
    pd.DataFrame(X_resampled, columns=feature_cols, index=range(len(X_resampled))),
    pd.Series(y_resampled, name="label_binary", index=range(len(X_resampled)), dtype=np.int32)
], axis=1)

print(f"    Final shape: {df_final.shape}")
print(f"    Features: {len(feature_cols)}")
print(f"    Samples: {len(df_final)}")
print(f"    label_binary dtype: {df_final['label_binary'].dtype}")

# ── Step 6: Train / Test split ───────────────────────────────────────────────

print(f"\n[6] Creating train/test split (80/20)...")
X_train, X_test, y_train, y_test, indices_train, indices_test = train_test_split(
    df_final[feature_cols],
    df_final["label_binary"],
    df_final.index,
    test_size=0.2,
    random_state=42,
    stratify=df_final["label_binary"]
)

# Create train and test dataframes
df_train = df_final.iloc[indices_train].copy().reset_index(drop=True)
df_test = df_final.iloc[indices_test].copy().reset_index(drop=True)

print(f"    Train set: {df_train.shape}")
print(f"      TB: {int(df_train['label_binary'].sum())} ({100*df_train['label_binary'].sum()/len(df_train):.1f}%)")
print(f"      Ctrl: {len(df_train)-int(df_train['label_binary'].sum())} ({100*(1 - df_train['label_binary'].sum()/len(df_train))*100:.1f}%)")
print(f"    Test set: {df_test.shape}")
print(f"      TB: {int(df_test['label_binary'].sum())} ({100*df_test['label_binary'].sum()/len(df_test):.1f}%)")
print(f"      Ctrl: {len(df_test)-int(df_test['label_binary'].sum())} ({100*(1 - df_test['label_binary'].sum()/len(df_test))*100:.1f}%)")

# ── Step 7: Save all datasets ────────────────────────────────────────────────

print(f"\n[7] Saving datasets...")

output_paths = {
    "tb_multimodal_integrated_final.csv": df_final,
    "tb_train_set.csv": df_train,
    "tb_test_set.csv": df_test
}

for fname, data in output_paths.items():
    path = OUT_DIR / fname
    data.to_csv(path, index=False)
    print(f"    → {path} ({data.shape})")

# ── Step 8: Save feature metadata ────────────────────────────────────────────

print(f"\n[8] Saving feature metadata...")

feature_metadata = {
    "total_features": len(feature_cols),
    "feature_categories": {
        "genomic_biomarkers": len([c for c in feature_cols if not any(x in c for x in ["pathway", "snp", "genetic", "humidity", "temperature", "AQI", "protein"])]),
        "pathways": len([c for c in feature_cols if "pathway" in c]),
        "snp_risk_scores": len([c for c in feature_cols if "snp" in c or "genetic" in c]),
        "environmental": len([c for c in feature_cols if any(x in c for x in ["humidity", "temperature", "AQI", "PM", "NO"])]),
        "serum_proteins": len([c for c in feature_cols if "protein" in c or c in ["CXCL10", "CRP", "SAA1", "IL6", "TNF", "IL1B", "IL8", "IFIT1", "IFIT3", "OAS1"]])
    },
    "sample_statistics": {
        "n_total": len(df_final),
        "n_train": len(df_train),
        "n_test": len(df_test),
        "n_tb": int(sum(df_final["label_binary"])),
        "n_control": int(len(df_final) - sum(df_final["label_binary"])),
        "pct_tb": float(100 * sum(df_final["label_binary"]) / len(df_final)),
        "pct_control": float(100 * (len(df_final) - sum(df_final["label_binary"])) / len(df_final))
    },
    "normalization": {
        "method": "StandardScaler",
        "mean": 0,
        "std": 1
    },
    "balancing": {
        "method": "SMOTE",
        "k_neighbors": 5,
        "synthetic_samples_added": n_synthetic
    }
}

metadata_path = OUT_DIR / "feature_metadata.json"
with open(metadata_path, "w") as f:
    json.dump(feature_metadata, f, indent=2)
print(f"    → {metadata_path}")

# ── Step 9: Save feature list ────────────────────────────────────────────────

feature_list_path = OUT_DIR / "feature_list.txt"
with open(feature_list_path, "w") as f:
    f.write("# Features in TB Multimodal Integrated Dataset\n\n")
    f.write(f"Total: {len(feature_cols)} features\n\n")
    for i, feat in enumerate(feature_cols, 1):
        f.write(f"{i:3d}. {feat}\n")
print(f"    → {feature_list_path}")

# ── Summary ──────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("Phase 3 Final — Integration Complete")
print("=" * 70)
print("\nGenerated Datasets:")
for fname, data in output_paths.items():
    print(f"\n  {fname}")
    print(f"    Shape: {data.shape}")
    print(f"    TB samples: {int(sum(data['label_binary']))}")
    print(f"    Control samples: {int(len(data) - sum(data['label_binary']))}")

print(f"\nFeatures by category:")
for cat, count in feature_metadata["feature_categories"].items():
    print(f"  {cat}: {count}")

print(f"\n✅ All datasets ready for Phase 4 (Transformer)")
print("=" * 70)
