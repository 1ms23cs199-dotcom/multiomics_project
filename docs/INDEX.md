# Documentation Index

**Last Updated:** March 18, 2026

This folder contains comprehensive guides for the Multi-Omics TB Insight Engine project.

---

## Main Documentation Files

### 1. **PHASE2B3_DOCUMENTATION.md** — Complete Phase 2B+3 Technical Report

**Purpose:** In-depth documentation of all feature engineering work, challenges overcome, and results.

**Contents:**
- Executive summary of Phase 2B+3
- Technical architecture and data flow diagrams
- Detailed breakdown of each feature engineering component:
  - Genomic biomarker selection (VarianceThreshold + SelectKBest)
  - SNP risk score engineering (Hardy-Weinberg genetics)
  - Serum proteomics integration (synthetic placeholder with PRIDE workflow)
  - Patient-level alignment (multi-omics fusion)
  - StandardScaler normalization (z-score)
  - SMOTE balancing (synthetic sample generation)
  - Train/test splitting (stratified 80/20)
- **5 Major Challenges & Solutions:**
  1. Immune pathway genes missing from top 50 biomarkers
  2. SNP column name mismatches
  3. Environmental data sparsity
  4. StandardScaler + SMOTE pipeline errors
  5. Label column type mismatches
- Results summary (final datasets, statistics)
- Known limitations and workarounds
- Phase 4 transformer requirements preview

**Best For:** Understanding HOW the data was processed, WHAT went wrong, and HOW to fix it

**Key Insights:**
- 112 engineered features from 5 modalities
- 616 samples (605 original + 11 SMOTE synthetic)
- Perfect 50/50 TB/Control balance
- All features normalized and validated
- Synthetic proteomics awaiting real PRIDE data

---

### 2. **DATASETS_GUIDE.md** — Comprehensive Data Dictionary & Usage Guide

**Purpose:** Quick reference for all available datasets, how to use them, and Phase 4–5 requirements.

**Contents:**
- **Available Datasets (9 total):**
  - `tb_multimodal_integrated_final.csv` (616 × 120) — primary balanced dataset
  - `tb_train_set.csv` (492 × 120) — 80% training split
  - `tb_test_set.csv` (124 × 120) — 20% held-out test split
  - Plus 6 intermediate/reference datasets
  
- **Column Descriptions:**
  - 8 metadata columns (patient_id, location, labels, etc.)
  - 50 genomic biomarkers (top genes by f-score)
  - 3 immune pathway aggregates (interferon, inflammatory, neutrophil)
  - 19 SNP risk scores (genetic burden)
  - 12 environmental variables (temperature, humidity, elevation, etc.)
  - 10 serum protein biomarkers (CXCL10, CRP, SAA1, IL6, TNF, etc.)

- **Phase 4: Transformer Encoder Requirements**
  - Input format (112 features × 492 samples)
  - Baseline architecture (2–4 encoder blocks, 8–16 attention heads)
  - Hyperparameter search space
  - Cross-validation strategy (5-fold StratifiedKFold)
  - Expected performance metrics (AUC > 0.85 target)
  - Feature importance extraction methods

- **Phase 5: Quantum Feature Selection Requirements**
  - Input: 32-dim Transformer embeddings
  - Objectives: Reduce to 8–10 features via quantum algorithms
  - Three quantum algorithm options (VQE, QAOA, Hybrid)
  - Quantum hardware recommendations (Qiskit simulator to start)
  - Expected outputs (feature list, quantum report, validation metrics)

- **Data Loading Templates**
  - pandas DataFrames
  - PyTorch TensorDataset and DataLoader
  - Feature metadata (JSON loading)

- **Quality Assurance Checklist**
  - Shape & size validation
  - Missing value checks
  - Class balance verification
  - Data type consistency
  - Feature scale verification (normalized)
  - Train/test leakage checks

**Best For:** Quick lookup of dataset specifics, integration with Phase 4 code, understanding data requirements

**Key Quick Facts:**
- 112 features (all normalized)
- 616 total samples (50% TB, 50% Control)
- 492 training / 124 test samples
- Zero missing values
- Ready for immediate ML use

---

## Quick Navigation

**For Project Overview:**
→ Start with main [README](../README.md) (if exists) or `data/DATASETS.md`

**For Phase 2B+3 Deep Dive:**
→ Read `PHASE2B3_DOCUMENTATION.md`
- Section: "Challenges & Solutions" if debugging issues
- Section: "Results & Outputs" for final dataset summary
- Section: "Known Limitations" for caveats

**For Phase 4 Transformer Development:**
→ Read `DATASETS_GUIDE.md`
- Section: "Available Datasets" → select dataset to load
- Section: "Phase 4: Transformer Encoder Requirements" → architecture & hyperparameters
- Section: "Data Loading Templates" → copy-paste code

**For Phase 5 Quantum Feature Selection:**
→ Read `DATASETS_GUIDE.md`
- Section: "Phase 5: Quantum Feature Selection Requirements" → algorithm options
- Section: "Phase 4 Output" (mentioned in Phase 5) → understand input format (32-dim embeddings)

**Quick Dataset Selection:**
| Use Case | Dataset |
|----------|---------|
| General exploration | `tb_multimodal_integrated_final.csv` |
| Phase 4 model training | `tb_train_set.csv` |
| Phase 4 final evaluation | `tb_test_set.csv` |
| Debugging/validation | `tb_multimodal_patient_matrix_raw.csv` (pre-normalization) |
| Genomic-only analysis | `genomic_biomarkers_selected.csv` |

---

## File Locations

```
multiomics_project/
├── docs/
│   ├── PHASE2B3_DOCUMENTATION.md        ← Technical deep-dive (THIS SESSION)
│   ├── DATASETS_GUIDE.md                ← Data dictionary + Phase 4–5 guide (THIS SESSION)
│   └── INDEX.md                         ← You are here
├── data/
│   ├── processed/
│   │   ├── tb_multimodal_integrated_final.csv    (616 × 120)
│   │   ├── tb_train_set.csv                      (492 × 120)
│   │   ├── tb_test_set.csv                       (124 × 120)
│   │   ├── feature_metadata.json
│   │   ├── feature_list.txt
│   │   ├── tb_multimodal_patient_matrix_raw.csv  (605 × 121, pre-normalization)
│   │   ├── genomic/
│   │   │   ├── genomic_biomarkers_selected.csv
│   │   │   ├── snp_risk_scores.csv
│   │   │   └── genomic_biomarker_importance.csv
│   │   └── proteomic/
│   │       ├── serum_proteomics_synthetic.csv
│   │       └── PROTEOMICS_PLACEHOLDER_NOTE.md
│   └── raw/ (original datasets)
├── scripts/
│   ├── feature_engineering_phase2b_genomic.py
│   ├── feature_engineering_phase2b_snp.py
│   ├── feature_engineering_phase2b_proteomics.py
│   ├── feature_engineering_phase_patient_alignment.py
│   └── feature_engineering_final_integration.py
└── README.md (project overview)
```

---

## Git Commit Reference

**Phase 2B+3 Complete:** Commit `6f0689e`

All feature engineering scripts, intermediate datasets, and final outputs committed. Ready for Phase 4 development.

---

## Contact & Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | March 18, 2026 | Initial documentation for Phase 2B+3 completion |

---

**Happy exploring! 🚀**
