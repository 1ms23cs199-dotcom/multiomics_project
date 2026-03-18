"""
feature_engineering_phase2b_genomic.py
======================================
Phase 2B — Genomic Feature Engineering

Implements:
1. Variance threshold filtering
2. SelectKBest differential gene selection (t-test based)
3. Pathway aggregation scores
4. Patient metadata extraction from processed data

Output: genomic_biomarkers_selected.csv (605 × 53 features)
        - 50 individual TB biomarkers
        - 3 immune pathway scores
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_classif
from scipy import stats

# ── Paths ────────────────────────────────────────────────────────────────────
GENOMIC_COMBINED = Path("data/processed/genomic/genomic_combined.csv")
OUT_DIR = Path("data/processed/genomic")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Define TB-relevant immune pathways ─────────────────────────────────────────
IMMUNE_PATHWAYS = {
    "interferon_response": [
        "IFIT1", "IFIT3", "OAS1", "MX1", "STAT1", "IRF1", "IRF7"
    ],
    "inflammatory_response": [
        "IL6", "TNF", "IL1B", "IL8", "IL10", "CXCL10"
    ],
    "neutrophil_activation": [
        "ELANE", "MPO", "LCN2", "AZU1", "CTSG"
    ]
}

# ── Step 1: Load genomic data ─────────────────────────────────────────────────

print("=" * 70)
print("Phase 2B — Genomic Feature Engineering")
print("=" * 70)

df = pd.read_csv(GENOMIC_COMBINED)
print(f"\n[1] Loaded genomic_combined.csv: {df.shape}")
print(f"    Sample IDs: {df['sample_id'].nunique()}")
print(f"    Labels: {df['label'].value_counts().to_dict()}")

# Separate features and metadata
meta_cols = ["sample_id", "label", "dataset", "split", "label_binary"]
gene_cols = [c for c in df.columns if c not in meta_cols]
X = df[gene_cols].copy()
y = df["label_binary"].copy()

print(f"    Features (genes): {X.shape[1]}")
print(f"    Samples: {X.shape[0]}")

# ── Step 2: Variance threshold filtering ──────────────────────────────────────

print("\n[2] Variance Threshold Filtering (threshold=0.01)")
selector_var = VarianceThreshold(threshold=0.01)
X_var = selector_var.fit_transform(X)
high_var_genes = X.columns[selector_var.get_support()].tolist()

print(f"    Before: {X.shape[1]} genes")
print(f"    After:  {X_var.shape[1]} genes")
print(f"    Removed: {X.shape[1] - X_var.shape[1]} low-variance genes")

# ── Step 3: SelectKBest differential selection ────────────────────────────────

print("\n[3] SelectKBest (f_classif) — Top 50 TB Biomarkers")
selector_kb = SelectKBest(score_func=f_classif, k=50)
X_selected = selector_kb.fit_transform(X_var, y)

# Get selected gene names
high_var_df = pd.DataFrame(X_var, columns=high_var_genes)
selected_mask = selector_kb.get_support()
selected_genes = high_var_df.columns[selected_mask].tolist()
scores = selector_kb.scores_[selected_mask]
feature_importance = sorted(zip(selected_genes, scores), key=lambda x: x[1], reverse=True)

print(f"    Selected genes: {len(selected_genes)}")
print(f"\n    Top 10 TB Biomarkers (by f-value):")
for i, (gene, score) in enumerate(feature_importance[:10], 1):
    print(f"      {i}. {gene:20s} f-score: {score:.2f}")

# ── Step 4: Pathway aggregation ──────────────────────────────────────────────

print("\n[4] Computing Immune Pathway Aggregation Scores")

pathway_scores = {}
for pathway_name, pathway_genes in IMMUNE_PATHWAYS.items():
    # Find which pathway genes are in our selected genes
    present_genes = [g for g in pathway_genes if g in selected_genes]
    print(f"    {pathway_name}:")
    print(f"      Target genes: {pathway_genes}")
    print(f"      Found in top 50: {present_genes}")
    
    if present_genes:
        # Create DataFrame with selected genes for easy indexing
        selected_df = pd.DataFrame(X_selected, columns=selected_genes)
        # Compute mean expression of pathway genes
        pathway_scores[pathway_name] = selected_df[present_genes].mean(axis=1).values
    else:
        # If no genes from pathway found, set to zero
        print(f"      ⚠ No genes from this pathway in top 50; using zeros")
        pathway_scores[pathway_name] = np.zeros(X_selected.shape[0])

# ── Step 5: Assemble final feature matrix ────────────────────────────────────

print("\n[5] Assembling Final Feature Matrix")

# Create dataframe with metadata + selected genes + pathway scores
result_df = df[["sample_id", "label", "label_binary", "dataset", "split"]].copy()

# Add selected genes
selected_df = pd.DataFrame(X_selected, columns=selected_genes, index=df.index)
result_df = pd.concat([result_df, selected_df], axis=1)

# Add pathway scores
for pathway_name, pathway_values in pathway_scores.items():
    result_df[f"pathway_{pathway_name}"] = pathway_values

print(f"    Final shape: {result_df.shape}")
print(f"    Columns: {result_df.columns.tolist()[:10]}... (showing first 10)")

# ── Step 6: Save outputs ─────────────────────────────────────────────────────

output_path = OUT_DIR / "genomic_biomarkers_selected.csv"
result_df.to_csv(output_path, index=False)
print(f"\n[6] Saved → {output_path}")

# Save feature importance
feature_importance_df = pd.DataFrame(feature_importance, columns=["gene", "f_score"])
feature_importance_df.to_csv(OUT_DIR / "genomic_biomarker_importance.csv", index=False)
print(f"    Saved feature importance → {OUT_DIR / 'genomic_biomarker_importance.csv'}")

# ── Summary ──────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("Phase 2B — Genomic Processing Complete")
print("=" * 70)
print(f"Output file: {output_path}")
print(f"Shape: {result_df.shape}")
print(f"Columns:")
print(f"  - Metadata: 5 (sample_id, label, label_binary, dataset, split)")
print(f"  - Gene biomarkers: {len(selected_genes)}")
print(f"  - Pathway scores: 3")
print(f"  - Total features: {result_df.shape[1] - 5}")
print(f"\nLabel distribution:")
print(result_df["label"].value_counts())
print("=" * 70)
