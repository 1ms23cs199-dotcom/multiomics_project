"""
preprocess_gwas.py  — Phase 2, Step 2d
=======================================
Filters the raw GWAS Catalog TSV for TB-associated SNPs using
p-value threshold < 5e-6, then encodes them as binary features
per sample based on chromosome position.

Input:  data/raw/genomic/gwas-association-downloaded_*.tsv
Output: data/processed/genomic/gwas_filtered_snps.csv

Usage:
    python scripts/preprocess_gwas.py
"""

import pathlib
import glob
import pandas as pd

BASE     = pathlib.Path(__file__).resolve().parent.parent
RAW      = BASE / "data" / "raw"       / "genomic"
OUT      = BASE / "data" / "processed" / "genomic"
OUT.mkdir(parents=True, exist_ok=True)

P_THRESH = 5e-6


def main():
    print("=" * 60)
    print("Phase 2 — GWAS SNP Filtering")
    print("=" * 60)

    # Find the GWAS file (name includes download date)
    matches = list(RAW.glob("gwas-association-downloaded*.tsv"))
    if not matches:
        raise FileNotFoundError(f"No GWAS TSV found in {RAW}")
    gwas_file = matches[0]
    print(f"\nLoading: {gwas_file.name}")

    df = pd.read_csv(gwas_file, sep="\t", low_memory=False)
    print(f"Raw shape: {df.shape}")
    print(f"Columns  : {df.columns.tolist()}\n")

    # ── Identify p-value column (name varies by download version) ──
    pval_col = None
    for candidate in ["P-VALUE", "PVALUE", "pvalue", "p_value", "P_VALUE"]:
        if candidate in df.columns:
            pval_col = candidate
            break
    if pval_col is None:
        # Try case-insensitive
        for col in df.columns:
            if "p-value" in col.lower() or "pvalue" in col.lower():
                pval_col = col
                break
    assert pval_col, f"Cannot find p-value column. Columns: {df.columns.tolist()}"
    print(f"P-value column: '{pval_col}'")

    # ── Coerce and filter ──────────────────────────────────────
    df[pval_col] = pd.to_numeric(df[pval_col], errors="coerce")
    before       = len(df)
    df_filtered  = df[df[pval_col] < P_THRESH].copy()
    after        = len(df_filtered)
    print(f"Rows before filter: {before:,}")
    print(f"Rows after  filter: {after:,}  (p < {P_THRESH:.0e})")

    # ── Select useful columns ──────────────────────────────────
    desired = [
        "SNPS", "CHR_ID", "CHR_POS", pval_col,
        "MAPPED_GENE", "STRONGEST SNP-RISK ALLELE",
        "RISK ALLELE FREQUENCY", "DISEASE/TRAIT", "PUBMEDID",
        "OR or BETA", "95% CI (TEXT)",
    ]
    available = [c for c in desired if c in df_filtered.columns]
    df_out    = df_filtered[available].reset_index(drop=True)

    # Rename for convenience
    df_out = df_out.rename(columns={
        "SNPS"                        : "snp_id",
        "CHR_ID"                      : "chromosome",
        "CHR_POS"                     : "position",
        pval_col                      : "p_value",
        "MAPPED_GENE"                 : "mapped_gene",
        "STRONGEST SNP-RISK ALLELE"   : "risk_allele",
        "RISK ALLELE FREQUENCY"       : "risk_allele_freq",
        "DISEASE/TRAIT"               : "trait",
        "PUBMEDID"                    : "pubmed_id",
        "OR or BETA"                  : "effect_size",
        "95% CI (TEXT)"               : "ci_95",
    })

    # Drop rows with no SNP ID
    df_out = df_out.dropna(subset=["snp_id"])

    # ── Save ──────────────────────────────────────────────────
    out_path = OUT / "gwas_filtered_snps.csv"
    df_out.to_csv(out_path, index=False)

    print(f"\nSaved → {out_path}")
    print(f"Shape : {df_out.shape}")
    print(f"\nTop 10 SNPs by p-value:")
    print(df_out.sort_values("p_value").head(10)[
        ["snp_id", "chromosome", "position", "p_value", "mapped_gene", "risk_allele"]
    ].to_string(index=False))
    print("=" * 60)


if __name__ == "__main__":
    main()
