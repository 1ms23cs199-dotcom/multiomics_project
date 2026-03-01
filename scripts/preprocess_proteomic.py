"""
preprocess_proteomic.py  — Phase 2, Step 2e
=============================================
Computes physicochemical feature descriptors for each H37Rv protein
from the UniProt FASTA file using Biopython ProteinAnalysis.

Features per protein (30 total):
  - Molecular weight, isoelectric point (pI), instability index,
    GRAVY (hydropathicity), aromaticity
  - Secondary structure fractions (helix, turn, sheet)
  - Amino acid composition (20 values)
  - Sequence length

Input:  data/raw/proteomic/uniprot_h37rv_sequences.fasta
        data/raw/proteomic/uniprot_h37rv_features.tsv   (metadata)
Output: data/processed/proteomic/proteomic_features.csv

Usage:
    python scripts/preprocess_proteomic.py
"""

import pathlib
import pandas as pd
import numpy as np
from Bio import SeqIO
from Bio.SeqUtils.ProtParam import ProteinAnalysis

BASE     = pathlib.Path(__file__).resolve().parent.parent
FASTA_IN = BASE / "data" / "raw"       / "proteomic" / "uniprot_h37rv_sequences.fasta"
TSV_IN   = BASE / "data" / "raw"       / "proteomic" / "uniprot_h37rv_features.tsv"
OUT_FILE = BASE / "data" / "processed" / "proteomic"  / "proteomic_features.csv"
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

AMINO_ACIDS = list("ACDEFGHIKLMNPQRSTVWY")


def analyse_sequence(record) -> dict | None:
    """Computes physicochemical features for one protein SeqRecord."""
    seq_str = str(record.seq).upper()

    # Remove ambiguous residues (X, B, Z, U, O) to avoid ProtParam errors
    valid_seq = "".join(aa for aa in seq_str if aa in AMINO_ACIDS)
    if len(valid_seq) < 10:
        return None

    try:
        pa = ProteinAnalysis(valid_seq)

        features = {
            "entry_id"          : record.id,
            "description"       : record.description[:120],
            "seq_length"        : len(valid_seq),
            "molecular_weight"  : round(pa.molecular_weight(), 2),
            "isoelectric_point" : round(pa.isoelectric_point(), 3),
            "instability_index" : round(pa.instability_index(), 3),
            "gravy"             : round(pa.gravy(), 4),
            "aromaticity"       : round(pa.aromaticity(), 4),
        }

        # Secondary structure fractions
        helix_f, turn_f, sheet_f = pa.secondary_structure_fraction()
        features["ss_helix"] = round(helix_f, 4)
        features["ss_turn"]  = round(turn_f,  4)
        features["ss_sheet"] = round(sheet_f, 4)

        # Amino acid composition (20 features, each 0–1)
        aa_comp = pa.get_amino_acids_percent()
        for aa in AMINO_ACIDS:
            features[f"aa_{aa}"] = round(aa_comp.get(aa, 0.0), 5)

        return features

    except Exception as exc:
        print(f"  Warning: skipping {record.id} — {exc}")
        return None


def main():
    print("=" * 60)
    print("Phase 2 — Proteomic Feature Extraction")
    print("=" * 60)

    if not FASTA_IN.exists():
        raise FileNotFoundError(f"Missing: {FASTA_IN}\nDownload from UniProt first.")

    records = list(SeqIO.parse(str(FASTA_IN), "fasta"))
    print(f"\nLoaded {len(records)} protein records from FASTA")

    rows    = []
    skipped = 0
    for rec in records:
        feat = analyse_sequence(rec)
        if feat:
            rows.append(feat)
        else:
            skipped += 1

    print(f"Successfully processed : {len(rows)}")
    print(f"Skipped (too short)    : {skipped}")

    df = pd.DataFrame(rows)

    # ── Merge UniProt metadata TSV if available ────────────────
    if TSV_IN.exists():
        print(f"\nMerging metadata TSV ...")
        meta = pd.read_csv(TSV_IN, sep="\t", low_memory=False)
        print(f"  TSV columns: {meta.columns.tolist()}")

        # UniProt FASTA IDs format: sp|ACCESSION|ENTRY_NAME
        df["_accession"] = df["entry_id"].str.extract(r"\|([^|]+)\|", expand=False)

        # Try merging on 'Entry' (standard UniProt TSV column)
        if "Entry" in meta.columns:
            df = df.merge(meta, left_on="_accession", right_on="Entry", how="left")
            print(f"  Merged on 'Entry' column: {df['Entry'].notna().sum()} matches")

        df.drop(columns=["_accession"], errors="ignore", inplace=True)

    # ── Normalise numeric features (MinMax to 0–1) ─────────────
    numeric_cols = [
        "seq_length", "molecular_weight", "isoelectric_point",
        "instability_index", "gravy", "aromaticity",
        "ss_helix", "ss_turn", "ss_sheet",
    ] + [f"aa_{aa}" for aa in AMINO_ACIDS]

    numeric_cols = [c for c in numeric_cols if c in df.columns]

    from sklearn.preprocessing import MinMaxScaler
    scaler             = MinMaxScaler()
    df[numeric_cols]   = scaler.fit_transform(df[numeric_cols].fillna(0))

    # ── Stability flag (instability_index > 0.5 after normalisation) ──
    # Raw threshold: > 40 = unstable (before scaling)
    # We add this flag using the raw value before scaling — recompute
    df_raw = pd.DataFrame(rows)
    df["is_unstable"] = (df_raw["instability_index"] > 40).astype(int)

    # ── Save ──────────────────────────────────────────────────
    df.to_csv(OUT_FILE, index=False)

    print(f"\nSaved → {OUT_FILE}")
    print(f"Shape : {df.shape}")
    print(f"\nSample (first 3 rows, key features):")
    display_cols = ["entry_id", "seq_length", "molecular_weight",
                    "isoelectric_point", "instability_index", "gravy", "is_unstable"]
    display_cols = [c for c in display_cols if c in df.columns]
    print(df[display_cols].head(3).to_string(index=False))

    print(f"\nUnstable proteins (instability_index > 40): {df['is_unstable'].sum()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
