"""
preprocess_genomic.py  — Phase 2, Step 2a-2c
==============================================
Parses all three GEO series matrix files, extracts sample labels,
maps Illumina probe IDs to gene names using GPL annotation files,
normalises expression values, and saves a unified feature matrix.

Outputs (all in data/processed/genomic/):
  - gse37250_processed.csv    expression + labels, gene columns
  - gse19435_processed.csv    expression + labels, gene columns
  - gse83456_processed.csv    expression + labels, gene columns
  - genomic_combined.csv      all three merged, train/val split flagged

Usage:
    python scripts/preprocess_genomic.py
"""

import gzip
import re
import pathlib
import numpy as np
import pandas as pd
from scipy import stats

# ── Paths ─────────────────────────────────────────────────────
BASE   = pathlib.Path(__file__).resolve().parent.parent
RAW    = BASE / "data" / "raw"    / "genomic"
OUT    = BASE / "data" / "processed" / "genomic"
OUT.mkdir(parents=True, exist_ok=True)

# ── How many top variable genes to keep (reduces memory) ─────
TOP_GENES = 5000   # top 5000 most variable probes → genes


# ═════════════════════════════════════════════════════════════
# STEP 1 — Parse annotation files (probe ID → gene symbol)
# ═════════════════════════════════════════════════════════════

def parse_soft_annotation(soft_gz: pathlib.Path) -> dict:
    """
    Reads a GEO GPL SOFT gzip file and returns {probe_id: gene_symbol}.
    Looks for the platform_table_begin section and then reads the
    ID and Symbol (or ILMN_Gene) columns.
    """
    probe_to_gene = {}
    print(f"  Parsing annotation: {soft_gz.name} ...", end=" ", flush=True)

    in_table = False
    header   = None

    with gzip.open(soft_gz, "rt", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.rstrip("\n")

            if line.startswith("!platform_table_begin"):
                in_table = True
                continue

            if line.startswith("!platform_table_end"):
                break

            if not in_table:
                continue

            cols = line.split("\t")

            # First line inside table is the header
            if header is None:
                header = [c.strip().upper() for c in cols]
                continue

            if len(cols) < 2:
                continue

            # Find index of probe ID column (always 'ID') and gene symbol
            if "ID" not in header:
                continue
            id_idx = header.index("ID")

            # Gene symbol column varies between GPL versions
            gene_idx = None
            for candidate in ["ILMN_GENE", "SYMBOL", "GENE_SYMBOL", "GENE"]:
                if candidate in header:
                    gene_idx = header.index(candidate)
                    break

            if gene_idx is None:
                continue

            probe_id = cols[id_idx].strip()
            gene_sym = cols[gene_idx].strip()

            if probe_id and gene_sym and gene_sym not in ("", "---", "NA"):
                probe_to_gene[probe_id] = gene_sym

    print(f"{len(probe_to_gene):,} probe→gene mappings loaded")
    return probe_to_gene


# ═════════════════════════════════════════════════════════════
# STEP 2 — Extract labels from GEO series matrix metadata
# ═════════════════════════════════════════════════════════════

# Label mapping rules: (field_name, {raw_value: binary_label or string_label})
LABEL_RULES = {
    "GSE37250": {
        "field"  : "disease state",
        "mapping": {
            "active tuberculosis" : "TB",
            "latent tb infection" : "LTBI",     # kept but flagged separately
            "other disease"       : "Control",
        },
    },
    "GSE19435": {
        "field"  : "illness",
        "mapping": {
            "ptb"     : "TB",
            "control" : "Control",
        },
    },
    "GSE83456": {
        "field"  : "disease state",
        "mapping": {
            "ptb"      : "TB",
            "eptb"     : "TB",      # Extra-Pulmonary TB → same TB class
            "hc"       : "Control",
            "sarcoid"  : "Other",   # kept but flagged
        },
    },
}


def extract_metadata(gz_path: pathlib.Path, gse_id: str):
    """
    Reads the series matrix header and returns:
      - sample_ids  : list of GSM accession strings
      - labels      : list of label strings aligned to sample_ids
    """
    rules    = LABEL_RULES[gse_id]
    field    = rules["field"]
    mapping  = rules["mapping"]

    sample_ids  = []
    labels_raw  = []
    found_label = False

    with gzip.open(gz_path, "rt", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.rstrip("\n")

            # Sample accession order
            if line.startswith("!Sample_geo_accession"):
                parts      = line.split("\t")
                sample_ids = [p.strip().strip('"') for p in parts[1:] if p.strip()]

            # Label row
            if "!Sample_characteristics_ch1" in line and field + ":" in line.lower() and not found_label:
                vals = re.findall(field + r":\s*([^\"\t]+)", line, re.IGNORECASE)
                labels_raw  = [v.strip().lower() for v in vals]
                found_label = True

            if line.startswith("!series_matrix_table_begin"):
                break

    if not labels_raw:
        print(f"  WARNING: No label column found for field '{field}' in {gse_id}")
        labels_raw = ["unknown"] * len(sample_ids)

    # Map raw labels to canonical labels
    labels = [mapping.get(l, "unknown") for l in labels_raw]

    print(f"  {gse_id}: {len(sample_ids)} samples | label counts: "
          + str(pd.Series(labels).value_counts().to_dict()))

    return sample_ids, labels


# ═════════════════════════════════════════════════════════════
# STEP 3 — Extract expression matrix from series matrix file
# ═════════════════════════════════════════════════════════════

def extract_expression(gz_path: pathlib.Path) -> pd.DataFrame:
    """
    Reads the data table portion of a GEO series matrix file.
    Returns a DataFrame: rows = probes, columns = GSM sample IDs.
    """
    print(f"  Reading expression matrix from {gz_path.name} ...", end=" ", flush=True)

    lines = []
    in_data = False

    with gzip.open(gz_path, "rt", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("!series_matrix_table_begin"):
                in_data = True
                continue
            if line.startswith("!series_matrix_table_end"):
                break
            if in_data:
                lines.append(line)

    # First line is the header (ID_REF, GSM...)
    from io import StringIO
    df = pd.read_csv(StringIO("\n".join(lines)), sep="\t", index_col=0,
                     low_memory=False, na_values=["NA", "null", ""])

    # Strip quotes from index and column names
    df.index   = df.index.str.strip('"')
    df.columns = df.columns.str.strip('"')

    print(f"{df.shape[0]:,} probes × {df.shape[1]} samples")
    return df


# ═════════════════════════════════════════════════════════════
# STEP 4 — Map probes → genes, normalise, select top variable
# ═════════════════════════════════════════════════════════════

def map_and_normalise(expr_df: pd.DataFrame, probe_map: dict,
                      top_n: int = TOP_GENES) -> pd.DataFrame:
    """
    1. Map probe IDs to gene symbols (drop unmapped)
    2. Average expression across probes sharing the same gene
    3. Log2 transform (if values look linear, i.e. max > 100)
    4. Z-score normalise across samples
    5. Keep top_n most variable genes
    """
    # 1. Map probes
    expr_df["gene"] = expr_df.index.map(probe_map)
    expr_df = expr_df.dropna(subset=["gene"])

    # 2. Average probes per gene
    expr_df = expr_df.groupby("gene").mean()

    # 3. Log2 transform if needed
    if expr_df.values.max() > 100:
        expr_df = np.log2(expr_df.clip(lower=1))

    # 4. Z-score per gene across samples
    expr_df = expr_df.apply(stats.zscore, axis=1, result_type="broadcast")

    # 5. Select top N most variable
    gene_var = expr_df.var(axis=1).sort_values(ascending=False)
    top_genes = gene_var.head(top_n).index
    expr_df = expr_df.loc[top_genes]

    print(f"  After mapping + filtering: {expr_df.shape[0]:,} genes × {expr_df.shape[1]} samples")
    return expr_df


# ═════════════════════════════════════════════════════════════
# STEP 5 — Process one GEO dataset end-to-end
# ═════════════════════════════════════════════════════════════

def process_gse(gse_id: str, gz_file: str, annotation_gz: str,
                split_tag: str) -> pd.DataFrame:
    """
    Full pipeline for one GEO dataset.
    Returns a sample × feature DataFrame with a 'label' column.
    """
    print(f"\n{'─'*60}")
    print(f"Processing {gse_id}  ({split_tag})")
    print(f"{'─'*60}")

    # Annotation
    probe_map = parse_soft_annotation(RAW / annotation_gz)

    # Labels
    sample_ids, labels = extract_metadata(RAW / gz_file, gse_id)

    # Expression matrix (probes × samples)
    expr = extract_expression(RAW / gz_file)

    # Align sample order with labels (some matrices may have extra columns)
    common_cols = [s for s in sample_ids if s in expr.columns]
    expr        = expr[common_cols]
    labels_aligned = [labels[sample_ids.index(s)] for s in common_cols]

    # Map, normalise, select top genes
    expr_mapped = map_and_normalise(expr, probe_map, top_n=TOP_GENES)

    # Transpose: samples × genes
    result = expr_mapped.T.copy()

    # Add metadata columns
    result.index.name = "sample_id"
    result["label"]   = labels_aligned
    result["dataset"] = gse_id
    result["split"]   = split_tag

    # Move metadata to front
    meta_cols = ["label", "dataset", "split"]
    result    = result[meta_cols + [c for c in result.columns if c not in meta_cols]]

    print(f"  Final shape: {result.shape[0]} samples × {result.shape[1]} columns")
    return result


# ═════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("Phase 2 — Genomic Preprocessing")
    print("=" * 60)

    # Check annotation files exist
    gpl6947  = RAW / "GPL6947_family.soft.gz"
    gpl10558 = RAW / "GPL10558_family.soft.gz"

    if not gpl6947.exists():
        raise FileNotFoundError(f"Missing: {gpl6947}\nRun download_datasets.py first.")
    if not gpl10558.exists():
        raise FileNotFoundError(
            f"Missing: {gpl10558}\n"
            "Download from: https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPL10nnn/GPL10558/soft/GPL10558_family.soft.gz"
        )

    # ── Process each dataset ──────────────────────────────────
    df37250 = process_gse(
        gse_id       = "GSE37250",
        gz_file      = "GSE37250_series_matrix.txt.gz",
        annotation_gz= "GPL10558_family.soft.gz",
        split_tag    = "train",
    )
    df37250.to_csv(OUT / "gse37250_processed.csv")
    print(f"  Saved → {OUT / 'gse37250_processed.csv'}")

    df19435 = process_gse(
        gse_id       = "GSE19435",
        gz_file      = "GSE19435_series_matrix.txt.gz",
        annotation_gz= "GPL6947_family.soft.gz",
        split_tag    = "validation",
    )
    df19435.to_csv(OUT / "gse19435_processed.csv")
    print(f"  Saved → {OUT / 'gse19435_processed.csv'}")

    df83456 = process_gse(
        gse_id       = "GSE83456",
        gz_file      = "GSE83456_series_matrix.txt.gz",
        annotation_gz= "GPL10558_family.soft.gz",
        split_tag    = "train",
    )
    df83456.to_csv(OUT / "gse83456_processed.csv")
    print(f"  Saved → {OUT / 'gse83456_processed.csv'}")

    # ── Find common genes across all three datasets ───────────
    print(f"\n{'─'*60}")
    print("Building combined matrix (common genes only) ...")

    # Gene columns only (exclude metadata cols)
    meta  = ["label", "dataset", "split"]
    genes37250 = set(df37250.columns) - set(meta)
    genes19435 = set(df19435.columns) - set(meta)
    genes83456 = set(df83456.columns) - set(meta)

    common_genes = sorted(genes37250 & genes19435 & genes83456)
    print(f"  Common genes across all three datasets: {len(common_genes):,}")

    # Subset each to common genes + metadata
    combined = pd.concat([
        df37250[meta + common_genes],
        df83456[meta + common_genes],
        df19435[meta + common_genes],
    ], axis=0)

    combined.index.name = "sample_id"

    # Drop 'unknown' labels and LTBI (ambiguous for binary TB model)
    before = len(combined)
    combined = combined[~combined["label"].isin(["unknown", "LTBI"])]
    print(f"  Rows after removing unknown/LTBI labels: {len(combined)} (removed {before - len(combined)})")

    # Binary label column: TB=1, Control=0, Other=0
    combined["label_binary"] = combined["label"].map(
        {"TB": 1, "Control": 0, "Other": 0}
    ).fillna(0).astype(int)

    combined.to_csv(OUT / "genomic_combined.csv")
    print(f"  Saved → {OUT / 'genomic_combined.csv'}")

    # ── Final summary ─────────────────────────────────────────
    print(f"\n{'='*60}")
    print("Genomic Preprocessing Complete")
    print(f"{'='*60}")
    print(f"  Total samples  : {len(combined)}")
    print(f"  Features (genes): {len(common_genes)}")
    print(f"  Label distribution:")
    print(combined["label"].value_counts().to_string())
    print(f"  Binary label (TB=1): {combined['label_binary'].sum()} TB | {(combined['label_binary']==0).sum()} Non-TB")
    print(f"\n  Output files in: {OUT}")
    print("=" * 60)


if __name__ == "__main__":
    main()
