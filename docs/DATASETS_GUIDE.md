# Datasets Guide: Available Datasets & Phase 4–5 Requirements

**Last Updated:** March 18, 2026  
**Status:** ✅ Phase 2B+3 Complete

---

## Table of Contents

1. [Available Datasets](#available-datasets)
2. [Column Descriptions](#column-descriptions)
3. [Phase 4: Transformer Encoder Requirements](#phase-4-transformer-encoder-requirements)
4. [Phase 5: Quantum Feature Selection Requirements](#phase-5-quantum-feature-selection-requirements)
5. [Data Loading Templates](#data-loading-templates)
6. [Quality Assurance](#quality-assurance)

---

## Available Datasets

### Production Datasets (Ready for Phase 4)

#### 1. **tb_multimodal_integrated_final.csv**

**Purpose:** Complete multi-omics dataset — all samples, normalized, SMOTE-balanced, ready for advanced modeling.

**Location:** `data/processed/tb_multimodal_integrated_final.csv`

**Shape:** 616 rows × 120 columns

**Sample Composition:**
- Original samples: 605 (605 TB + Control patients)
- SMOTE synthetic: 11 (interpolated TB samples for perfect balance)
- TB class: 308 (50.0%)
- Control class: 308 (50.0%)

**Column Breakdown:**
```
Columns 1-8:   Metadata (patient identifiers, location, labels)
Columns 9-58:  Genomic biomarkers (50 genes selected by SelectKBest)
Columns 59-61: Immune pathway aggregation (3 pathways)
Columns 62-80: SNP risk scores (19 GWAS SNPs)
Columns 81-92: Environmental variables (12 features)
Columns 93-102: Serum proteins (10 biomarkers)
```

**Data Characteristics:**
- Normalization: StandardScaler (z-score)
- Feature scale: mean ≈ 0, std ≈ 1
- Missing values: 0 (all imputed)
- Data types: 112 float64 (features), 6 string (metadata), 2 int64 (labels)

**When to Use:**
✅ General exploration and full-resource model training  
❌ Do NOT use if different train/test split needed (use tb_train_set.csv + tb_test_set.csv instead)

**Typical Usage:**
```python
import pandas as pd
import numpy as np

df = pd.read_csv('tb_multimodal_integrated_final.csv')

# Separate metadata and features
metadata_cols = ['patient_id', 'sample_id_full', 'city', 'year', 
                 'label', 'label_binary', 'dataset', 'split']
feature_cols = [c for c in df.columns if c not in metadata_cols]

X = df[feature_cols].values  # 616 × 112 numpy array
y = df['label_binary'].values  # 616 binary labels

print(f"X shape: {X.shape}, y shape: {y.shape}")
print(f"TB ratio: {sum(y==1)/len(y):.2%}")
```

---

#### 2. **tb_train_set.csv**

**Purpose:** 80% training split for model development and hyperparameter tuning.

**Location:** `data/processed/tb_train_set.csv`

**Shape:** 492 rows × 120 columns

**Sample Composition:**
- Total: 492 samples
- TB cases: 246 (50.0%)
- Control cases: 246 (50.0%)
- Source: 80% stratified sample from tb_multimodal_integrated_final.csv

**Data Characteristics:**
- Normalization: StandardScaler (inherited from final dataset)
- Stratification: Label distribution preserved (50/50)
- Random state: 42 (reproducible splits)

**When to Use:**
✅ Primary training for Phase 4 Transformer encoder  
✅ Cross-validation / hyperparameter optimization  
✅ Feature importance analysis

**⚠️ Important:** Do NOT use test set to make train/test split decisions!

**Typical Usage (Phase 4):**
```python
import pandas as pd
from sklearn.model_selection import StratifiedKFold

df_train = pd.read_csv('tb_train_set.csv')
X_train = df_train.drop(columns=['patient_id', 'sample_id_full', 'city', 
                                  'year', 'label', 'label_binary', 'dataset', 'split'])
y_train = df_train['label_binary'].values

# 5-fold cross-validation for hyperparameter tuning
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
for fold, (train_idx, val_idx) in enumerate(skf.split(X_train, y_train)):
    X_fold_train = X_train.iloc[train_idx].values
    y_fold_train = y_train[train_idx]
    X_fold_val = X_train.iloc[val_idx].values
    y_fold_val = y_train[val_idx]
    
    # Train Transformer on fold_train, evaluate on fold_val
    print(f"Fold {fold}: train={len(y_fold_train)}, val={len(y_fold_val)}")
```

---

#### 3. **tb_test_set.csv**

**Purpose:** 20% held-out test split for final model evaluation (no leakage).

**Location:** `data/processed/tb_test_set.csv`

**Shape:** 124 rows × 120 columns

**Sample Composition:**
- Total: 124 samples
- TB cases: 62 (50.0%)
- Control cases: 62 (50.0%)
- Source: 20% stratified sample from tb_multimodal_integrated_final.csv

**Data Characteristics:**
- Normalization: StandardScaler (consistent with training data)
- Stratification: Label distribution preserved (50/50)
- Random state: 42 (matches train_test_split seed)

**When to Use:**
✅ Final model evaluation ONLY (after Phases 4–5 complete)  
✅ Report test accuracy, AUC, precision, recall, F1  
❌ Do NOT use during model training or hyperparameter selection (causes overfitting)

**Typical Usage (Final Evaluation):**
```python
import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score

df_test = pd.read_csv('tb_test_set.csv')
X_test = df_test.drop(columns=['patient_id', 'sample_id_full', 'city', 
                                'year', 'label', 'label_binary', 'dataset', 'split'])
y_test = df_test['label_binary'].values

# After training Phase 4 Transformer and Phase 5 feature selection:
y_pred = phase5_model.predict(X_test)  # Final model predictions

print(classification_report(y_test, y_pred))
print(f"Test AUC-ROC: {roc_auc_score(y_test, y_pred_proba):.4f}")
```

---

### Intermediate Datasets (For Validation & Debugging)

#### 4. **tb_multimodal_patient_matrix_raw.csv**

**Purpose:** Pre-normalization patient matrix — useful for debugging, feature analysis, and understanding intermediate processing steps.

**Location:** `data/processed/tb_multimodal_patient_matrix_raw.csv`

**Shape:** 605 rows × 121 columns

**Content:**
- Original 605 patients (pre-SMOTE)
- Raw feature values (before StandardScaler)
- 1,044 NaN values (environmental data sparsity) — imputed with column mean later

**Column Order:**
```
1-9:   Metadata
10-59:   Genomic biomarkers (50 genes)
60-62:   Pathways (3 aggregates)
63-81:   SNP risk scores (19)
82-93:   Environmental (12)
94-103: Serum proteins (10)
```

**When to Use:**
✅ Validate StandardScaler effect (compare raw to normalized features)  
✅ Inspect NaN imputation (locate which features had missing values)  
✅ Debug feature distributions before/after normalization  
❌ Do NOT use for Phase 4 training (not normalized, class imbalance)

**Typical Usage:**
```python
import pandas as pd
import matplotlib.pyplot as plt

df_raw = pd.read_csv('tb_multimodal_patient_matrix_raw.csv')
df_final = pd.read_csv('tb_multimodal_integrated_final.csv')

# Compare distributions of a feature (e.g., C2 gene)
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].hist(df_raw['C2'], bins=30, alpha=0.7, label='Raw')
axes[1].hist(df_final['C2'], bins=30, alpha=0.7, label='Normalized')
plt.show()
```

---

### Feature Catalogs

#### 5. **feature_metadata.json**

**Purpose:** Machine-readable summary of feature composition and dataset statistics.

**Location:** `data/processed/feature_metadata.json`

**Content:**
```json
{
  "version": "1.0",
  "created_date": "2026-03-18",
  "total_features": 112,
  "by_category": {
    "genomic_biomarkers": 50,
    "immune_pathways": 3,
    "snp_risk_scores": 19,
    "environmental_variables": 12,
    "serum_proteins": 10
  },
  "normalization": "StandardScaler (z-score)",
  "samples": {
    "total": 616,
    "original": 605,
    "synthetic_smote": 11,
    "label_distribution": {
      "TB": 308,
      "Control": 308,
      "ratio": 0.5
    }
  },
  "splits": {
    "train": 492,
    "test": 124
  }
}
```

**When to Use:**
✅ Quick reference for feature counts by modality  
✅ Automated feature preprocessing (e.g., load feature counts in Phase 5 algorithm)  
✅ Version tracking across project phases

**Usage Example:**
```python
import json

with open('feature_metadata.json', 'r') as f:
    meta = json.load(f)

total_features = meta['total_features']
genomic_genes = meta['by_category']['genomic_biomarkers']
smote_synthetic = meta['samples']['synthetic_smote']

print(f"Total features: {total_features}")
print(f"Genomic genes: {genomic_genes}")
print(f"SMOTE synthetic samples: {smote_synthetic}")
```

---

#### 6. **feature_list.txt**

**Purpose:** Human-readable line-by-line listing of all 112 features with indices for model interpretation.

**Location:** `data/processed/feature_list.txt`

**Format:**
```
Index 0: ASPRV1
Index 1: C2
Index 2: CEACAM8
...
Index 49: ZCWPW1
Index 50: interferon_response (pathway)
Index 51: inflammatory_response (pathway)
Index 52: neutrophil_activation (pathway)
Index 53: rs123456 (SNP risk score)
...
Index 102: OAS1 (protein)
```

**When to Use:**
✅ Identify feature names when analyzing model weights/attention  
✅ Create feature importance plots with readable labels  
✅ Cross-reference Phase 5 selected features to original names

**Usage Example:**
```python
# Load feature names
with open('feature_list.txt', 'r') as f:
    feature_names = [line.strip() for line in f if line.strip()]

import numpy as np
from scipy.stats import rankdata

# After Phase 4 Transformer training, extract feature importance
feature_importance = model.compute_feature_importance(X_test)  # 112 scores
top_10_indices = np.argsort(feature_importance)[-10:]

print("Top 10 Most Important Features:")
for idx in reversed(top_10_indices):
    print(f"  {idx}: {feature_names[idx]}")
```

---

### Reference Datasets (For Context & Validation)

#### 7. **genomic_biomarkers_selected.csv**

**Purpose:** Genomic features only (50 selected genes + 3 pathways) — intermediate output from Phase 2B.

**Location:** `data/processed/genomic/genomic_biomarkers_selected.csv`

**Shape:** 605 rows × 58 columns (metadata + 50 genes + 3 pathways)

**When to Use:**
✅ Validate gene selection process  
✅ Analyze genomic signal in isolation  
✅ Create genomic-only baseline model (for Phase 4 ablation)

---

#### 8. **snp_risk_scores.csv**

**Purpose:** SNP risk features only (19 genetic variants) — intermediate output from Phase 2B.

**Location:** `data/processed/genomic/snp_risk_scores.csv`

**Shape:** 605 rows × 20 columns (sample_id + 19 SNP features)

**When to Use:**
✅ Analyze genetic risk score distribution  
✅ Create SNP-only baseline model  
✅ Correlation analysis between SNP scores and TB status

---

#### 9. **serum_proteomics_synthetic.csv**

**Purpose:** Serum proteomics features (10 TB biomarkers) — SYNTHETIC placeholder awaiting real PRIDE data.

**Location:** `data/processed/proteomic/serum_proteomics_synthetic.csv`

**Shape:** 605 rows × 11 columns (sample_id + 10 proteins)

**⚠️ CRITICAL NOTE:** Data is SYNTHETIC (lognormal-generated). See `PROTEOMICS_PLACEHOLDER_NOTE.md` for real data integration workflow.

**Proteins Included:**
- CXCL10 (chemokine)
- CRP (acute phase)
- SAA1 (acute phase)
- IL6 (pro-inflammatory)
- TNF (pro-inflammatory)
- IL1B (pro-inflammatory)
- IL8 (chemotactic)
- IFIT1 (antiviral)
- IFIT3 (antiviral)
- OAS1 (antiviral)

---

## Column Descriptions

### Metadata Columns (8 total)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `patient_id` | str | Unique patient identifier | "GSM914000" |
| `sample_id_full` | str | Original GEO sample accession | "GSM914353" |
| `city` | str | City (randomized if no true metadata available) | "New York" |
| `year` | int | Year of sampling | 2018 |
| `label` | str | TB status (text) | "TB" |
| `label_binary` | int | TB status (binary): 1=TB, 0=Control | 1 |
| `dataset` | str | Source dataset name | "GSE37250" |
| `split` | str | Data split allocation | "train" |

---

### Genomic Biomarkers (50 genes)

**Selection Method:** VarianceThreshold(0.01) + SelectKBest(f_classif, k=50)

**Top 5 Genes by f-score:**
| Gene | f-score | Function |
|------|---------|----------|
| C2 | 158.46 | Complement cascade, innate immunity |
| KCNJ15 | 57.53 | Potassium channel, metabolism |
| ASPRV1 | 36.37 | Serine protease, immune response |
| DNAJB7 | 29.28 | Heat shock protein, cellular stress |
| TUBA4A | 23.91 | Tubulin, cytoskeleton |

**All 50 genes:** See Column Names in imported DataFrame or `feature_list.txt`

**Scale:** Normalized (z-score): mean=0, std=1

**Interpretation:** Positive values = higher expression in TB relative to population mean

---

### Immune Pathways (3 aggregates)

| Pathway | Genes Included | Description |
|---------|----------------|-------------|
| `interferon_response` | IFIT1, IFIT3, OAS1, STAT1, ISGF3G, etc. | Type I/II interferon signaling (antiviral) |
| `inflammatory_response` | IL6, TNF, IL1B, IL8, CCL2, CXCL10, etc. | Pro-inflammatory cytokines (innate) |
| `neutrophil_activation` | S100A12, CEACAM8, FCGR1A, etc. | Granulocyte infiltration & activation |

**Scoring Method:** Mean expression of pathway genes from top 50 biomarkers

**⚠️ Current Status:** All pathways score ~0 (target genes not selected by SelectKBest)

**Interpretation:** If non-zero, higher values indicate pathway activation in TB patients

---

### SNP Risk Scores (19 features)

**Source:** 20 GWAS SNPs filtered by p-value < 1e-5 and clinical relevance

**Construction:** Individual genetic burden scores per SNP
- Effect size (odds ratio or beta) × Hardy-Weinberg genotype probability
- Aggregated into population genetic burden score

**Example SNP Features:**
```
rs123456_risk
rs789012_risk
...
genetic_burden_score (cumulative)
```

**Values:** Normalized (z-score): mean≈0, std≈0.5

**Interpretation:** Positive = increased TB susceptibility; Negative = protective alleles

---

### Environmental Variables (12 features)

**Linking:** City-year level, merged to patient locations

| Variable | Scale | Sparsity | Notes |
|----------|-------|----------|-------|
| Temperature (mean) | °C | 17% NaN | Filled with population mean |
| Temperature (max) | °C | 17% NaN | " |
| Temperature (min) | °C | 17% NaN | " |
| Humidity (mean) | % | 17% NaN | " |
| Precipitation | mm | 17% NaN | " |
| Elevation | m | 0% NaN | Complete data |
| Population density | people/km² | 0% NaN | Complete data |
| Urban index | [0-1] | 0% NaN | Urbanization proxy |
| PM2.5 | µg/m³ | 17% NaN | Air quality proxy |
| GDP per capita | USD | 0% NaN | Economic development |
| Healthcare access | score | 0% NaN | Distance to nearest clinic |
| Year | int | 0% NaN | Temporal marker |

**Scale:** Normalized (z-score): mean=0, std=1

**⚠️ Caveat:** Random city/year assignment may not reflect actual patient location

**Interpretation:** Positive values = higher environmental burden (e.g., higher pollution, lower temperature for TB transmission)

---

### Serum Protein Biomarkers (10 features)

⚠️ **DATA STATUS:** Currently SYNTHETIC; awaiting real PRIDE human serum proteomics

| Protein | Abbreviation | Biological Role | Expected Level in TB |
|---------|--------------|-----------------|----------------------|
| C-X-C Motif Chemokine 10 | CXCL10 | Immune cell recruitment | ↑ Elevated |
| C-Reactive Protein | CRP | Acute phase response | ↑ Elevated |
| Serum Amyloid A1 | SAA1 | Acute phase response | ↑ Elevated |
| Interleukin-6 | IL6 | Pro-inflammatory | ↑ Elevated |
| Tumor Necrosis Factor-alpha | TNF | Pro-inflammatory | ↑ Elevated |
| Interleukin-1 Beta | IL1B | Pro-inflammatory | ↑ Elevated |
| Interleukin-8 | IL8 | Chemotactic | ↑ Elevated |
| Interferon-Induced Protein | IFIT1 | Antiviral | ↑ Elevated |
| Interferon-Induced Protein | IFIT3 | Antiviral | ↑ Elevated |
| Oligoadenylate Synthetase 1 | OAS1 | Antiviral | ↑ Elevated |

**Scale:** Log2 intensity (synthetic) — will change upon PRIDE integration

**Interpretation:** Higher values = higher protein abundance / stronger immune activation in TB patients

---

## Phase 4: Transformer Encoder Requirements

### Input Data Format

**Dataset:** `tb_train_set.csv` (492 samples) + `tb_test_set.csv` (124 samples)

**Feature Matrix Shape:** (N, 112)
- N = number of samples (492 for training)
- 112 = total engineered features

**Label Vector Shape:** (N,)
- 0 = Control
- 1 = Tuberculosis

**Data Characteristics:**
- Normalization: Already applied (StandardScaler)
- Missing values: Zero
- Class distribution: 50% TB, 50% Control (SMOTE-balanced)
- Data type: float32 or float64

---

### Transformer Architecture Recommendations

#### Baseline Architecture

```
Input Layer: 112 features
   ↓
Encoder Block 1:
  Multi-Head Self-Attention (8 heads, dim=64)
  Feed-Forward (FFN: 64 → 256 → 64)
  Residual connections + Layer Normalization
  Dropout (p=0.2)
  Output: (N, 64)
   ↓
Encoder Block 2:
  Multi-Head Self-Attention (4 heads, dim=32)
  Feed-Forward (32 → 128 → 32)
  Residual + Layer Norm
  Dropout (p=0.2)
  Output: (N, 32)
   ↓
Classification Head:
  Fully Connected: 32 → 16 (ReLU)
  Dropout (p=0.1)
  Fully Connected: 16 → 1 (Sigmoid)
   ↓
Output: TB probability [0, 1]
```

#### Hyperparameter Search Space

| Parameter | Recommended Range | Default |
|-----------|-------------------|---------|
| Embedding dimension | 32, 64, 128 | 64 |
| Num. encoder layers | 2, 3, 4 | 3 |
| Num. attention heads | 4, 8, 16 | 8 |
| FFN hidden dimension | 256, 512 | 256 |
| Dropout | 0.1, 0.2, 0.3 | 0.2 |
| Learning rate | 1e-3, 1e-4, 1e-5 | 1e-4 |
| Batch size | 16, 32, 64 | 32 |
| Optimizer | Adam, AdamW | Adam (lr=1e-4) |
| Loss function | BCEWithLogitsLoss | BCEWithLogitsLoss |
| Epochs | 50–200 | 100 |
| Early stopping patience | 10–20 | 15 |

---

### Expected Performance Metrics

**Baseline Expectations (from literature on similar TB datasets):**
- Training accuracy: >95%
- Validation accuracy: 80–90%
- Test accuracy: 80–90%
- AUC-ROC: 0.85–0.95
- F1 score: 0.80–0.90

**Success Criteria (Phase 4 → Phase 5):**
- Test AUC-ROC > 0.85
- Test F1 > 0.80
- Validation stability (low variance across CV folds)

---

### Cross-Validation Strategy

**Recommended:** 5-fold Stratified K-Fold on training data

```python
from sklearn.model_selection import StratifiedKFold

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

cv_scores = []
for fold, (train_idx, val_idx) in enumerate(skf.split(X_train, y_train)):
    X_fold_train = X_train[train_idx]
    y_fold_train = y_train[train_idx]
    X_fold_val = X_train[val_idx]
    y_fold_val = y_train[val_idx]
    
    # Train Transformer model
    model = TransformerEncoder(...)
    model.fit(X_fold_train, y_fold_train, 
              validation_data=(X_fold_val, y_fold_val),
              epochs=100, batch_size=32)
    
    # Evaluate fold
    val_auc = model.evaluate(X_fold_val, y_fold_val)
    cv_scores.append(val_auc)
    print(f"Fold {fold}: AUC = {val_auc:.4f}")

print(f"Mean CV AUC: {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")
```

---

### Learnings for Feature Importance

**Post-Training Analysis:**
1. Extract attention weights from encoder layers
   - Which features receive highest attention?
   - Do they match SelectKBest results?

2. Compute gradient-based feature importance (saliency)
   - Backprop input perturbations
   - Identify features affecting TB prediction

3. Compare to SelectKBest baseline
   - Are Transformer-learned features similar to f-classif selected genes?
   - If different, may indicate novel non-linear patterns

**Expected Insight:** Transformer may weight immune and genetic features heavily; environmental features may be downweighted.

---

## Phase 5: Quantum Feature Selection Requirements

### Input: Phase 4 Transformer Outputs

**Feature Space:** Transformer embeddings from final hidden layer

**Source:**
- Train set embeddings: (492, 32)
- Test set embeddings: (124, 32)
- Label vector: 616 binary TB/Control labels

**Format:** numpy arrays or PyTorch tensors

```python
# Extract Transformer embeddings
embeddings_train = transformer_model.encode(X_train)  # (492, 32)
embeddings_test = transformer_model.encode(X_test)    # (124, 32)
y_train = df_train['label_binary'].values              # (492,)
y_test = df_test['label_binary'].values                # (124,)
```

---

### Quantum Feature Selection Objectives

**Primary Goal:** Reduce 32-dimensional embedding space to ~5–10 most informative dimensions using quantum algorithms.

**Rationale:**
1. **Dimensionality Reduction:** 32 → 8 = 75% feature compression
2. **Quantum Advantage:** Quantum algorithms (VQE, QAOA) may find superior feature subsets vs. classical methods
3. **Clinical Interpretability:** Fewer features easier to validate and deploy
4. **Computational Efficiency:** Smaller models reduce inference latency

---

### Quantum Algorithm Options

#### Option A: Variational Quantum Eigensolver (VQE) with Ansatz

**Concept:** Train parameterized quantum circuit to learn feature importance scores

**Framework:**
```
Ansatz Circuit (quantum):
  Input: 32 qubits (one per embedding dimension)
        ↓
  Variational Layer (RY rotations parameterized by θ)
        ↓
  Entangling Layer (CNOT gates)
        ↓
  Measurement: Expectation value E(θ)
        ↓
Classical Optimizer (COBYLA):
  Minimize: |E(θ) − f_target|
  Where f_target = TB classification accuracy
        ↓
  Converged parameters θ* define feature importance
```

**Pros:** Native quantum approach, good for small feature spaces  
**Cons:** NISQ (noisy intermediate-scale) limitations, may require many circuit evaluations

**Hyperparameters:**
- Num. qubits: 32 (one per embedding dimension)
- Ansatz depth: 2–4
- Num. rotation parameters: 64–128
- Optimizer: COBYLA, SLSQP
- Max evaluations: 1000–5000

---

#### Option B: Quantum Approximate Optimization Algorithm (QAOA)

**Concept:** Approximate classical optimization problem (feature selection as MaxCut) with quantum circuit

**Framework:**
```
Problem Encoding:
  Feature selection = MaxCut problem on correlation graph
  32 features → 32 qubits
  Correlations between features → edge weights
        ↓
QAOA Circuit:
  Init: Equal superposition of all 2^32 states
  Problem Hamiltonian: Penalty for selecting correlated features
  Mixer Hamiltonian: Exploration of state space
  Sweep angles (β, γ) for depth-p circuit
        ↓
Measurement:
  Sample bitstring → feature mask (1 = selected, 0 = discarded)
  Repeat 1000 times → distribution of high-quality solutions
        ↓
Classical Post-processing:
  Select top K features from distribution
  Validate on test set
```

**Pros:** Well-motivated problem formulation, good for feature selection  
**Cons:** Requires large number of qubits (32), circuit complexity grows with depth

**Hyperparameters:**
- Num. qubits: 32
- Circuit depth (p): 2–5
- Num. angle sweeps: 100–500
- Num. measurement shots: 1024–10000
- K features to select: 8–12

---

#### Option C: Hybrid Quantum-Classical (Recommended for Near-Term)

**Concept:** Use quantum algorithm for candidate feature generation; classical optimizer for final ranking

**Workflow:**
```
Step 1: Classical Pre-screening
  Compute classical feature importance (gradient-based, MDI)
  Rank 32 embedding dimensions by importance
  Select top 20 candidates
        ↓
Step 2: Quantum Feature Selection (VQE/QAOA on top 20)
  Train quantum circuit to distinguish TB vs Control
  using selected 20 features
  Extract learned feature weights
        ↓
Step 3: Classical Refinement
  Rerank features by quantum-learned importance
  Select top 8–10 features
        ↓
Step 4: Validation
  Train simple classifier (logistic regression) on 8 features
  Evaluate on test set
  Compare performance vs. Phase 4 full 32-dim model
```

**Expected Outcome:**
- 8 selected features
- Test AUC: 80–85% (75–80% of 32-dim performance acceptable)
- Computational speedup: 4x reduction in inference

---

### Quantum Hardware / Simulator Recommendations

| Provider | Platform | Qubits | Type | Recommended For |
|----------|----------|--------|------|-----------------|
| IBM | Qiskit + Simulator | 32+ | Simulator | Development & testing |
| IBM | Qiskit + Hardware | 20–127 | NISQ | Production small instances |
| Rigetti | Forest / QCS | 30+ | Simulator & Hardware | Hybrid circuits |
| D-Wave | Leap | 5000 | Annealer | Large QUBO problems |
| Amazon | Braket | Multiple | Simulator & Hardware | Cloud-based access |

**For Phase 5 MVP:** Start with Qiskit Simulator (free, no queue time)

---

### Expected Outputs (Phase 5)

1. **Selected Features** (8–10 dimensions from original 32)
   ```
   embedding_dim_3
   embedding_dim_7
   embedding_dim_12
   embedding_dim_15
   embedding_dim_21
   embedding_dim_28
   embedding_dim_31
   embedding_dim_5
   ```

2. **Quantum Algorithm Report**
   - Circuit diagrams (ansatz & entanglement pattern)
   - Convergence history (optimization loss vs. iteration)
   - Feature importance scores from quantum circuit
   - Classical vs. quantum comparison

3. **Validation Metrics**
   - Test AUC-ROC on 8 selected features
   - Precision, recall, F1 on test set
   - Comparison table (32-dim vs. 8-dim performance)

4. **Final Model**
   - Logistic regression or simple neural network trained on 8 features
   - Deployment-ready (< 1MB model size)
   - Inference latency: < 1ms per sample

---

## Data Loading Templates

### Loading Production Datasets

**Python (pandas):**
```python
import pandas as pd
import numpy as np

# Load final integrated dataset
df_final = pd.read_csv('tb_multimodal_integrated_final.csv')
X_final = df_final.drop(columns=['patient_id', 'sample_id_full', 'city', 
                                  'year', 'label', 'label_binary', 'dataset', 'split']).values
y_final = df_final['label_binary'].values

# OR load pre-split train/test
df_train = pd.read_csv('tb_train_set.csv')
df_test = pd.read_csv('tb_test_set.csv')

X_train = df_train.drop(columns=['patient_id', 'sample_id_full', 'city', 
                                  'year', 'label', 'label_binary', 'dataset', 'split']).values
y_train = df_train['label_binary'].values

X_test = df_test.drop(columns=['patient_id', 'sample_id_full', 'city', 
                                'year', 'label', 'label_binary', 'dataset', 'split']).values
y_test = df_test['label_binary'].values

print(f"Train shape: {X_train.shape}, Test shape: {X_test.shape}")
```

**PyTorch TensorDataset:**
```python
import torch
from torch.utils.data import TensorDataset, DataLoader

# Convert to PyTorch tensors
X_train_tensor = torch.FloatTensor(X_train)
y_train_tensor = torch.LongTensor(y_train)

X_test_tensor = torch.FloatTensor(X_test)
y_test_tensor = torch.LongTensor(y_test)

# Create datasets
train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
test_dataset = TensorDataset(X_test_tensor, y_test_tensor)

# Create dataloaders
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

for X_batch, y_batch in train_loader:
    print(f"Batch shape: {X_batch.shape}, {y_batch.shape}")
    break
```

---

### Loading Feature Metadata

**Load feature counts:**
```python
import json

with open('feature_metadata.json', 'r') as f:
    metadata = json.load(f)

print(f"Total features: {metadata['total_features']}")
print(f"Genomic: {metadata['by_category']['genomic_biomarkers']}")
print(f"SNPs: {metadata['by_category']['snp_risk_scores']}")
print(f"Environmental: {metadata['by_category']['environmental_variables']}")
print(f"Proteins: {metadata['by_category']['serum_proteins']}")
```

**Load feature names:**
```python
with open('feature_list.txt', 'r') as f:
    feature_names = [line.strip() for line in f if line.strip()]

print(f"Total features: {len(feature_names)}")
print(f"First 10: {feature_names[:10]}")
```

---

## Quality Assurance

### Data Integrity Checks

**Before Phase 4 training, verify:**

```python
import pandas as pd
import numpy as np

df_train = pd.read_csv('tb_train_set.csv')
df_test = pd.read_csv('tb_test_set.csv')

# Check 1: Shape and size
assert df_train.shape[0] == 492, "Train size mismatch"
assert df_test.shape[0] == 124, "Test size mismatch"
assert df_train.shape[1] == 120, "Column count mismatch"

# Check 2: No missing values
assert df_train.isnull().sum().sum() == 0, "NaNs in training data"
assert df_test.isnull().sum().sum() == 0, "NaNs in test data"

# Check 3: Class balance
assert (df_train['label_binary'].sum() / len(df_train)) > 0.48, "Train imbalance"
assert (df_test['label_binary'].sum() / len(df_test)) > 0.48, "Test imbalance"

# Check 4: Data type consistency
feature_cols = [c for c in df_train.columns if c not in 
                ['patient_id', 'sample_id_full', 'city', 'year', 'label', 'label_binary', 'dataset', 'split']]
for col in feature_cols:
    assert df_train[col].dtype in [np.float64, np.float32], f"{col} not numeric"

# Check 5: Feature scale (should be normalized ~0 mean, ~1 std)
X_train = df_train[feature_cols].values
assert abs(X_train.mean()) < 0.1, f"Mean not centered: {X_train.mean()}"
assert abs(X_train.std() - 1.0) < 0.1, f"Std not scaled: {X_train.std()}"

# Check 6: No data leakage (verify train and test are disjoint)
train_patients = set(df_train['patient_id'].values)
test_patients = set(df_test['patient_id'].values)
assert len(train_patients & test_patients) == 0, "Train/test patients overlap!"

print("✅ All quality checks passed!")
```

---

### Performance Benchmarks

| Phase | Task | Expected Metric | Threshold |
|-------|------|-----------------|-----------|
| 4 | Transformer training | Validation AUC | > 0.85 |
| 4 | Transformer final | Test AUC | > 0.80 |
| 5 | Quantum selection | Selected features | 8–10 |
| 5 | Quantum final | Test AUC (8 features) | > 0.75 |

---

## Support & Documentation

For additional information, refer to:
- **Phase 2B+3 Details:** `docs/PHASE2B3_DOCUMENTATION.md`
- **Feature Engineering Scripts:** `scripts/feature_engineering_phase2b_*.py`
- **Intermediate Datasets:** `data/processed/genomic/`, `data/processed/proteomic/`

---

**Document Last Updated:** March 18, 2026  
**Status:** ✅ Ready for Phase 4 Development
