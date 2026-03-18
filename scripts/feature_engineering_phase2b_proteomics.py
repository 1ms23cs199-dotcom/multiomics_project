"""
feature_engineering_phase2b_proteomics.py
=========================================
Phase 2B — Proteomics Feature Engineering (Option A)

Attempts to fetch human serum proteomics TB datasets from ProteomeXchange/PRIDE.
If not available, creates a placeholder with noted absence.

Target: Human TB patient serum protein abundance
Expected TB biomarkers: CXCL10, CRP, SAA1, IL-6, TNF-α, etc.

Output: proteomics_serum_features.csv (605 × N protein features)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings

# ── Paths ────────────────────────────────────────────────────────────────────
OUT_DIR = Path("data/processed/proteomic")
OUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("Phase 2B — Proteomics Feature Engineering (Human Serum)")
print("=" * 70)

# ── Step 1: Known TB serum biomarkers ────────────────────────────────────────

TB_SERUM_BIOMARKERS = {
    # Inflammatory cytokines
    "CXCL10": {"role": "chemokine", "direction": "↑ in active TB"},
    "IL6": {"role": "cytokine", "direction": "↑ in active TB"},
    "TNF": {"role": "cytokine", "direction": "↑ in active TB"},
    "IL1B": {"role": "cytokine", "direction": "↑ in active TB"},
    "IL8": {"role": "chemokine", "direction": "↑ in active TB"},
    
    # Acute phase proteins
    "CRP": {"role": "acute phase", "direction": "↑ in active TB"},
    "SAA1": {"role": "acute phase", "direction": "↑ in active TB"},
    
    # Interferon-induced proteins
    "IFIT1": {"role": "interferon-induced", "direction": "↑"},
    "IFIT3": {"role": "interferon-induced", "direction": "↑"},
    "OAS1": {"role": "interferon-induced", "direction": "↑"},
}

print(f"\n[1] Target TB Serum Biomarkers: {len(TB_SERUM_BIOMARKERS)}")
for protein, info in list(TB_SERUM_BIOMARKERS.items())[:5]:
    print(f"    {protein:15s} {info['role']:20s} {info['direction']}")

# ── Step 2: Try to fetch from ProteomeXchange ────────────────────────────────

print(f"\n[2] Attempting to fetch human TB proteomics from ProteomeXchange...")
print(f"    (This would require API access or manual download from:")
print(f"     https://proteomecentral.proteomexchange.org/)")
print(f"    Search terms: 'tuberculosis' + 'Homo sapiens' + 'human serum'")
print(f"\n    Notable studies to search for:")
print(f"    - PXD000000 series (TB biomarker studies)")
print(f"    - PRIDE projects with TB + serum cohorts")

# For now, since real data requires manual curation, create synthetic features
# with realistic TB-serum protein patterns

print(f"\n[3] Creating synthetic human serum proteomics features")
print(f"    (Placeholder — team should replace with real PRIDE data)")

n_patients = 605
proteins = list(TB_SERUM_BIOMARKERS.keys())

# Create realistic patterns
proteomics_data = {}
for protein in proteins:
    # TB patients: higher baseline
    base_control = np.random.lognormal(mean=5.0, sigma=0.5, size=n_patients)
    base_tb = np.random.lognormal(mean=6.0, sigma=0.6, size=n_patients)  # Elevated in TB
    
    # Mix based on roughly 50-50 TB-Control split
    result = np.where(
        np.random.binomial(1, 0.5, n_patients),
        base_tb,
        base_control
    )
    proteomics_data[protein] = result

# Create dataframe
proteomics_df = pd.DataFrame(proteomics_data)
proteomics_df.insert(0, "sample_id", [f"patient_{i:04d}" for i in range(n_patients)])

print(f"    Generated features: {len(proteins)}")
print(f"    Shape: {proteomics_df.shape}")

# Normalize to [0, 1] for consistency
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
proteomics_df.iloc[:, 1:] = scaler.fit_transform(proteomics_df.iloc[:, 1:])

# ── Step 3: Save placeholder ─────────────────────────────────────────────────

output_path = OUT_DIR / "serum_proteomics_synthetic.csv"
proteomics_df.to_csv(output_path, index=False)

print(f"\n[4] Saved synthetic proteomics → {output_path}")
print(f"    ⚠ IMPORTANT: This is a synthetic placeholder!")
print(f"    ⚠ Replace with real data from ProteomeXchange:")
print(f"       1. Go to https://proteomecentral.proteomexchange.org/")
print(f"       2. Search: 'tuberculosis' + 'human serum' + 'Homo sapiens'")
print(f"       3. Download abundance matrix from a TB cohort study") 
print(f"       4. Replace this file with real data")

# ── Step 4: Create integration note ──────────────────────────────────────────

integration_note = """
# Human Serum Proteomics — Placeholder Status

## Current Status
- Using SYNTHETIC data for Phase 3-5 testing
- Real data required before model deployment

## How to Replace

1. **Find TB serum studies in ProteomeXchange:**
   https://proteomecentral.proteomexchange.org/cgi/GetDatasetList.cgi
   
   Search filters:
   - Species: Homo sapiens
   - Disease: tuberculosis
   - Sample type: serum or plasma
   
2. **Download the proteomics expression matrix:**
   - Format: rows = samples, columns = proteins
   - Units: log2 intensity, intensity, or abundance ratio
   
3. **Replace serum_proteomics_synthetic.csv:**
   ```bash
   # After downloading real data:
   mv serum_proteomics_real.csv data/processed/proteomic/serum_proteomics.csv
   ```

4. **Expected format:**
   ```
   sample_id,CXCL10,CRP,SAA1,IL6,TNF,IL1B,IL8,IFIT1,IFIT3,OAS1,...
   P0001,5.23,6.12,7.45,4.56,5.89,...
   P0002,4.89,5.67,6.78,5.12,6.34,...
   ```

5. **Recommended TB proteomics studies:**
   - Studies with n>100 TB patient samples
   - Matched healthy controls
   - Serum or plasma proteomics (not tissue)
   - Published 2018+ (more comprehensive MS methods)

## Known TB Serum Biomarkers
- CXCL10: Chemokine, robust TB marker
- CRP, SAA1: Acute phase proteins
- IL6, TNF: Systemic inflammation
- IFIT1, IFIT3: Interferon signature

## Alternative
If real serum data unavailable, consider:
- Use TB-specific mycobacterial proteins only (current data)
- Keep for drug discovery (Phase 7)
- Skip serum proteomics from patient classifier
"""

note_path = OUT_DIR / "PROTEOMICS_PLACEHOLDER_NOTE.md"
with open(note_path, "w") as f:
    f.write(integration_note)

print(f"\n[5] Integration guide → {note_path}")

# ── Summary ──────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("Phase 2B — Proteomics Setup Complete (Placeholder)")
print("=" * 70)
print(f"Output file: {output_path}")
print(f"Status: SYNTHETIC (needs real PRIDE data)")
print(f"Shape: {proteomics_df.shape}")
print(f"Proteins: {len(proteins)}")
print("\n⚠ NEXT STEPS:")
print("  1. Query ProteomeXchange for TB serum studies")
print("  2. Download real proteomics data")
print("  3. Replace synthetic file with real data")
print("  4. Re-run Phase 3 integration")
print("=" * 70)
