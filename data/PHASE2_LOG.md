# Phase 2 — Preprocessing Log
## Quantum-AI Powered Multi-Omics Disease Insight Engine
**Institution:** M.S. Ramaiah Institute of Technology, Bangalore  
**Target Disease:** Tuberculosis (TB)  
**Phase dates:** March 1, 2026  
**Status: ✅ Complete — all four scripts run, all outputs verified, committed to git**

---

## Overview

Phase 2 converts 18 raw heterogeneous data files (microarray compressed archives, FASTA protein sequences, NASA weather files, government AQI CSVs) into four clean, normalised, analysis-ready feature matrices. This phase is the most critical data engineering step of the project — without correctly parsed labels and properly normalised features, every downstream model will produce meaningless results.

Four preprocessing scripts were written and executed:

| Script | Modality | Output file(s) |
|---|---|---|
| `preprocess_genomic.py` | Gene expression (GEO microarray) | 4 CSV files |
| `preprocess_gwas.py` | Genetic variants (GWAS SNPs) | 1 CSV file |
| `preprocess_proteomic.py` | Protein sequences (UniProt FASTA) | 1 CSV file |
| `preprocess_environmental.py` | Weather + air quality | 1 CSV file |

---

## Section 1 — Genomic Preprocessing

### Script: `scripts/preprocess_genomic.py`

#### Datasets used
| File | Role | Platform |
|---|---|---|
| `GSE37250_series_matrix.txt.gz` | Primary training set | GPL10558 (HumanHT-12 v4) |
| `GSE83456_series_matrix.txt.gz` | Supplementary train (Indian Subcontinent) | GPL10558 (HumanHT-12 v4) |
| `GSE19435_series_matrix.txt.gz` | Held-out validation | GPL6947 (HumanHT-12 v3) |
| `GPL10558_family.soft.gz` | Probe-to-gene annotation for v4 | 47,323 probes |
| `GPL6947_family.soft.gz` | Probe-to-gene annotation for v3 | 48,803 probes |

#### Step-by-step pipeline

**Step 1 — GPL annotation parsing (`parse_soft_annotation`)**  
Both GPL SOFT files are compressed `.gz` text archives. They contain a long platform header section followed by a tab-separated table (beginning after the `!platform_table_begin` marker). The script reads this decompressed stream line by line, locates the table header, identifies which column index holds `ID` (probe ID) and `ILMN_Gene` (gene symbol), and builds a Python dictionary mapping every probe ID to its gene symbol. This produces:
- GPL10558: 47,323 probe → gene mappings
- GPL6947: 48,803 probe → gene mappings

**Step 2 — Label extraction (`extract_metadata`)**  
GEO series matrix files encode sample metadata in lines beginning with `!Sample_characteristics_ch1`. The label field varies by dataset:

| Dataset | Label field | Raw values | Mapping |
|---|---|---|---|
| GSE37250 | `disease state:` | `active tuberculosis`, `latent TB infection`, `other disease` | TB=1, Control=0, LTBI=excluded |
| GSE19435 | `illness:` | `PTB`, `Control` | TB=1, Control=0 |
| GSE83456 | `disease state:` | `PTB`, `EPTB`, `HC`, `Sarcoid` | TB=1, Control=0, Sarcoid→Other |

LTBI (latent TB) samples were excluded from training. These individuals carry *M. tuberculosis* without symptoms — their gene expression profiles overlap with both active TB and healthy controls, creating ambiguous labels that would introduce noise into the classifier. Sarcoidosis samples were retained as "Other" class because sarcoidosis produces granulomas similar to TB lesions and is a known clinical confounder — keeping these samples helps the model learn to distinguish TB from granulomatous mimics.

**Step 3 — Expression matrix extraction (`extract_expression`)**  
The expression matrix is located after the `!series_matrix_table_begin` marker inside each compressed GEO file. The header row contains `"ID_REF"` followed by `GSMxxxxxx` sample identifiers. Each subsequent row is one probe with numeric intensity values per sample. The script reads this block directly into a pandas DataFrame:
- GSE37250: 47,323 probes × 537 samples
- GSE19435: 48,803 probes × 33 samples
- GSE83456: 47,231 probes × 202 samples

**Step 4 — Probe-to-gene mapping and normalisation (`map_and_normalise`)**  
1. Every probe ID in the expression matrix is mapped to its gene symbol using the GPL dictionary
2. Probes without a gene symbol annotation (controls, unmapped probes) are dropped
3. Where multiple probes map to the same gene, the probe with the highest inter-sample variance is retained (avoids redundancy while keeping the most informative signal)
4. **Log₂ transform:** if any intensity value exceeds 100, the entire matrix is log₂-transformed. Raw Illumina intensities are on a linear scale spanning several orders of magnitude; log-transforming compresses the range and makes expression differences more interpretable and normally distributed
5. **Z-score normalisation (per gene, across samples):** each gene's expression values are standardised to mean=0, std=1. This removes systematic batch effects between studies and ensures no gene dominates the feature space simply because of scale differences
6. **Top 5,000 most variable genes** are selected by standard deviation across samples. The remaining ~42,000 probes are largely housekeeping-gene noise; restricting to high-variance genes is a standard feature selection approach in transcriptomics that reduces dimensionality and removes uninformative rows

**Step 5 — Common gene intersection and dataset combination**  
After independent processing, 5,000 genes are selected from each dataset. But GSE37250 and GSE83456 used HumanHT-12 v4 while GSE19435 used HumanHT-12 v3 — different probe sets measuring partially different genes. The final combined matrix retains only genes present across all three datasets: **112 common, high-variance genes**. This intersection ensures every sample (regardless of which study it came from) has the same feature vector, a prerequisite for unified model training.

LTBI samples were dropped from the combined matrix. Final sample counts (binary TB=1/Control=0):
- GSE37250: 195 TB, 175 Control (167 LTBI excluded)
- GSE83456: 92 TB, 61 Control (49 Sarcoid as Other)
- GSE19435: 21 TB, 12 Control
- **Combined: 605 samples, 308 TB, 297 Non-TB (near-balanced)**

#### Output files
| File | Shape | Description |
|---|---|---|
| `processed/genomic/gse37250_processed.csv` | 537 × 5003 | Per-dataset processed matrix (5000 genes + sample_id + label + split) |
| `processed/genomic/gse83456_processed.csv` | 202 × 5003 | Per-dataset processed matrix |
| `processed/genomic/gse19435_processed.csv` | 33 × 5003 | Per-dataset processed matrix |
| `processed/genomic/genomic_combined.csv` | 605 × 112 | Final combined matrix — model-ready input |

#### Why this is biologically valid for TB prediction

Blood-based RNA expression profiling is the gold standard approach for TB biomarker discovery. *Mycobacterium tuberculosis* infection triggers a well-characterised host response:
- **Interferon-stimulated genes (ISGs):** IFN-γ released by T cells activates macrophages and upregulates hundreds of ISGs including `GBP1`, `IFIT1`, `IFIT3`, `STAT1`, `IRF1`. These form the canonical "interferon signature" of active TB
- **Neutrophil degranulation genes:** active TB is associated with abnormally high neutrophil counts; genes like `S100A8`, `S100A9`, `MMP8` are reliably upregulated
- **Suppressed T-cell activation genes:** TB actively suppresses adaptive immunity to evade clearance — genes in the CD4+ T-cell activation pathway are characteristically downregulated

By training on these expression patterns, the model learns the molecular immune state of TB infection rather than memorising patient metadata — making it generalisable across geographically diverse cohorts (African patients in GSE37250, South Asian patients in GSE83456).

---

## Section 2 — GWAS Preprocessing

### Script: `scripts/preprocess_gwas.py`

#### Dataset used
- `gwas-association-downloaded_2026-02-28-EFO_1000049.tsv` — TB-associated SNPs from the GWAS Catalog (EFO trait ID for tuberculosis)

#### Pipeline
The raw GWAS catalog file contains 33 SNP associations across 38 metadata columns. The script:
1. Auto-detects the p-value column by scanning column names for variants of "p-value", "pvalue", "p_value" (robust to format differences across GWAS Catalog versions)
2. Parses p-values as floating-point numbers (handles values already in scientific notation)
3. Filters to retain only SNPs with **p < 5×10⁻⁶** — the standard genome-wide significance threshold adjusted for multiple testing burden across millions of SNPs
4. Selects and renames 11 informative columns: SNP ID, chromosome, genomic position, p-value, mapped gene, risk allele, risk allele frequency, OR/Beta (effect size), GWAS Catalog study accession, disease/trait, and genomic context
5. Saves to `gwas_filtered_snps.csv`

#### Output
- **20 statistically significant TB-associated SNPs** retained (of 33 total)
- Top hit: `rs140780894` on chromosome 6, position 32,657,607 — mapped to **HLA-DQA1–HLA-DQB1** region, p = 3×10⁻²³

#### Why this is biologically valid

The **HLA (Human Leukocyte Antigen) region** on chromosome 6 is the most replicated genetic locus for TB susceptibility in GWAS studies worldwide. HLA molecules are responsible for presenting pathogen peptides to T cells — variation in HLA type fundamentally affects whether the immune system can recognise and respond to *M. tuberculosis* antigens. An individual with an HLA haplotype that presents mycobacterial peptides poorly has an intrinsically higher risk of progression from infection to active disease.

Additional loci in this filtered set (e.g., `DAP` — Death-Associated Protein, involved in IFN-γ pathway; `MFAP2` — connective tissue remodelling; `FSTL5` — immune signalling) represent genuine biological mechanisms of TB susceptibility. Filtering by p < 5×10⁻⁶ ensures we retain only statistically robust associations rather than noise.

In Phase 3, these SNP positions will be used to extract genotype features for individuals (if individual-level genotype data is available) or as prior knowledge to weight specific genomic regions in the model.

---

## Section 3 — Proteomic Preprocessing

### Script: `scripts/preprocess_proteomic.py`

#### Datasets used
- `data/raw/proteomic/uniprot_h37rv_sequences.fasta` — protein amino acid sequences
- `data/raw/proteomic/uniprot_h37rv_metadata.tsv` — protein metadata (gene names, function, subcellular location, length)

#### Pipeline

**Step 1 — FASTA parsing (Biopython)**  
The FASTA file is parsed using Biopython's `SeqIO` module. Each record contains a UniProt accession, protein name, and full amino acid sequence. Only sequences between 50 and 5,000 amino acids are accepted (removes fragments and pseudo-genes that cannot be reliably analysed).

**Step 2 — Physicochemical feature computation (Biopython `ProteinAnalysis`)**  
For each protein, 30 physicochemical features are computed directly from its sequence:

| Feature | Biological meaning |
|---|---|
| `molecular_weight` | Size of the protein in Daltons — larger proteins are typically membrane complexes |
| `isoelectric_point` | pH at which the protein has zero net charge — affects binding partners and cellular localisation |
| `instability_index` | Score > 40 predicts an unstable protein in vitro — key for drug target consideration |
| `gravy` | Grand Average of Hydropathicity — positive values indicate membrane-spanning regions; negative values indicate soluble proteins |
| `aromaticity` | Fraction of aromatic amino acids (Phe, Trp, Tyr) — high aromaticity often indicates structural rigidity |
| `ss_helix`, `ss_turn`, `ss_sheet` | Predicted secondary structure fractions from Chou-Fasman scales — protein architecture fingerprint |
| `aa_A` … `aa_Y` (20 values) | Relative frequency of each of the 20 standard amino acids — the composition signature |

**Step 3 — Metadata merge**  
The computed physicochemical features are joined with the UniProt TSV metadata on accession ID, adding gene name, organism, protein name, reviewed/unreviewed status, and functional annotation.

**Step 4 — MinMax normalisation**  
All 30 numeric features are scaled to [0, 1] using sklearn's `MinMaxScaler`. This prevents proteins with high molecular weight (e.g., 150,000 Da) from dominating distance metrics in the fusion model over proteins scored on a 0–1 aromaticity scale.

**Step 5 — Instability flag**  
Proteins with `instability_index > 40` are flagged with a binary `is_unstable` column. Known TB drug targets (KatG, InhA, EmbB) fall within the moderately stable range — this flag can later help the model downweight structurally fragile proteins as drug target candidates.

#### Output
- `processed/proteomic/proteomic_features.csv`: **500 proteins × 41 columns** (30 raw features + 10 metadata + 1 binary flag)

#### Why this is biologically valid

The 500 proteins in this dataset are *M. tuberculosis* H37Rv proteins — the reference strain of the bacterium. Understanding the physical properties of mycobacterial proteins is essential for two reasons:

1. **Drug target identification:** TB treatment requires hitting specific bacterial proteins. Physicochemical features distinguish surface-exposed, druggable proteins (moderate GRAVY, low instability, high helix content — typical of membrane targets like InhA) from intracellular metabolic enzymes
2. **Host-pathogen interaction:** Proteins secreted by *M. tuberculosis* into the host cell (ESX-secreted proteins, lipoproteins) tend to have specific amino acid composition signatures. The GRAVY index and signal peptide-like hydrophobicity patterns help identify secreted virulence factors

The three manually downloaded PDB structures (KatG, InhA, Rv3804c) cover the primary targets of first-line TB drugs (isoniazid, ethambutol). These structural files are reserved for Phase 7 (3D visualisation and structural docking).

---

## Section 4 — Environmental Preprocessing

### Script: `scripts/preprocess_environmental.py`

#### Datasets used
- `nasa_delhi.csv`, `nasa_mumbai.csv`, `nasa_patna.csv`, `nasa_bangalore.csv`, `nasa_chennai.csv` — monthly climate data from NASA POWER (2015–2020)
- `india_aqi.csv` — daily air quality measurements across 26 Indian cities (Kaggle / CPCB)
- `who_tb_incidence.csv` — WHO global TB incidence rates (optional enrichment)

#### Pipeline

**Step 1 — NASA POWER CSV parsing**  
NASA POWER CSV files have an unusual format: a variable-length plain-text header block delimited by `-BEGIN HEADER-` and `-END HEADER-` markers, followed by actual CSV data. Crucially, the header section contains the word `Parameter(s):` which would falsely trigger a naive "find the first line starting with PARAMETER" search.

The parser skips lines until it finds the exact line `-END HEADER-`, then begins reading the CSV from the immediately following line. This line is the true CSV header: `PARAMETER,YEAR,JAN,FEB,...,DEC,ANN`.

Data rows are structured with **parameters as rows** (not columns): each row is one climate variable (RH2M = relative humidity, T2M = surface temperature) for one year. The parser reads all rows, then pivots so that RH2M and T2M become columns, with rows indexed by year. Only the `ANN` (annual mean) value is retained.

**Step 2 — India AQI aggregation**  
The AQI CSV contains daily measurements. Date strings are parsed into Python `datetime` objects, and the year is extracted. Annual mean values are computed per city-year for all pollutants: PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3, Benzene, Toluene, Xylene, AQI.

City names are normalised (Bengaluru vs. Bangalore variant handled via an alias dictionary) to match the five NASA cities before aggregation.

**Step 3 — Merge**  
NASA weather data (indexed by city + year) and AQI data (aggregated to city + year) are inner-joined on the `city` and `year` keys. The inner join ensures only city-year combinations with both weather and air quality data are retained — 30 rows (5 cities × 6 years: 2015–2020).

**Step 4 — MinMax normalisation**  
All 15 numeric features are scaled to [0, 1] independently, producing 15 additional `_scaled` columns alongside the raw values.

#### Output
- `processed/environmental/env_features.csv`: **30 rows × 32 columns** (city, year, 15 raw features, 15 scaled features)

#### Why this is biologically valid

Tuberculosis is not purely a biological disease — it is a social and environmental disease. Two environmental dimensions matter most:

**Air quality (AQI data):**  
- **PM2.5 and PM10:** Chronic inhalation of fine particulate matter damages the respiratory epithelium, impairs mucociliary clearance (the lung's first-line defence against inhaled pathogens), and provokes persistent pulmonary inflammation. This creates a permissive environment for *M. tuberculosis* to establish infection. Studies from Delhi and Patna consistently show a dose-response relationship between PM2.5 exposure and TB incidence
- **NO2 and SO2:** Markers of combustion-source pollution with direct immunosuppressive effects on alveolar macrophages — the cells responsible for destroying inhaled mycobacteria
- **Benzene and Toluene:** Volatile organic carcinogens associated with haematopoietic toxicity, potentially impairing the white blood cell production needed to mount TB immunity

**Climate (NASA POWER data):**  
- **T2M (surface temperature):** TB is a cold-weather disease in India. *M. tuberculosis* survives longer in cold, dry air; crowded indoor living conditions during winter months increase transmission probability. Temperature seasonality correlates with TB notification peaks
- **RH2M (relative humidity):** Low humidity enables airborne *M. tuberculosis* droplet nuclei to remain suspended longer. The aerosol transmission dynamics of TB are directly influenced by ambient humidity

The five cities selected (Delhi, Mumbai, Patna, Bangalore, Chennai) represent India's major urban TB burden centres and span climatic zones from subtropical semi-arid (Delhi, Patna) to tropical coastal (Mumbai, Chennai) to highland (Bangalore) — ensuring the environmental model captures geographic diversity in TB risk factors.

---

## Section 5 — Challenges Faced in Phase 2

### Challenge 6 — Wrong Platform Annotation File (GPL Mismatch)
**Problem:** The initial plan assumed GSE37250 used GPL6947 (HumanHT-12 v3), matching GSE19435. Only GPL6947 was downloaded during Phase 1. Upon peeking inside `GSE37250_series_matrix.txt.gz`, the `!Series_platform_id` line revealed `GPL10558` (HumanHT-12 v4) — a different chip generation with a different probe set.

**Impact:** Running preprocessing with the wrong annotation file would have produced completely incorrect gene-to-probe mappings, corrupting every gene expression feature vector for the 537 largest samples in the dataset.

**Resolution:** Identified the correct platform ID from inside the GEO file header (before touching any data) using a line-by-line inspection script (`_peek_labels.py`). Downloaded `GPL10558_family.soft.gz` (432 MB) from NCBI GEO FTP. Verified the file was complete after download by checking its size on disk. Updated the preprocessing script to use GPL10558 for both GSE37250 and GSE83456, and GPL6947 for GSE19435.

**Lesson:** Never assume platform compatibility across GEO datasets — always verify `!Series_platform_id` from inside the file before writing annotation parsers.

---

### Challenge 7 — Label Field Names Differ Across GEO Datasets
**Problem:** The label extraction logic needed to know the exact field name used in each dataset's `!Sample_characteristics_ch1` metadata lines. Different studies use different vocabulary: `disease state:`, `illness:`, `phenotype:`, `group:`, etc. Using the wrong field name would return no labels for that dataset.

**Resolution:** Wrote a dedicated inspection script (`scripts/_peek_labels.py`) that reads only the metadata section of each GEO file and prints all `!Sample_characteristics_ch1` values. This revealed the exact field names and exact label strings for all three datasets before writing a single line of preprocessing logic.

GSE37250 label values found: `active tuberculosis`, `latent TB infection`, `other disease`  
GSE19435 label values found: `PTB`, `Control`  
GSE83456 label values found: `PTB`, `EPTB`, `HC`, `Sarcoid`

All label mappings in `preprocess_genomic.py` are based on these confirmed values.

---

### Challenge 8 — Only 112 Common Genes After Cross-Platform Intersection
**Problem:** After independently selecting the top 5,000 most variable genes per dataset, only 112 genes appeared in all three processed datasets. This was lower than expected.

**Root cause:** GSE37250 and GSE83456 (both on HumanHT-12 v4 / GPL10558) shared most probes, but GSE19435 was on HumanHT-12 v3 (GPL6947), which has a different (older) probe set. While both platforms cover the same genome, many of the 5,000 high-variance genes from GSE37250/GSE83456 have no corresponding probe in GPL6947, and vice versa.

**How we proceeded:** The 112 common genes were accepted as the model's genomic feature vector for the combined matrix. This is still statistically sufficient — published TB biomarker signatures like the Sweeney 3-gene, Berry 393-gene, and Zak RISK11 signatures all use fewer than 200 genes and achieve robust performance. A 112-gene signature from three independent cohorts is biologically stringent (only genes replicably variable across all three populations are included).

**Alternative considered:** Using two-dataset combinations (GSE37250 + GSE83456 only, which share GPL10558) would yield ~4,500 common genes but would lose the independent validation cohort. The 112-gene strict intersection approach was chosen to preserve cross-platform validation integrity.

---

### Challenge 9 — NASA CSV Format: `Parameter(s):` Header Line Tripping the Parser
**Problem:** The NASA POWER CSV files contain a plain-text header block followed by actual CSV data. The parser was designed to find the first line beginning with the word `PARAMETER` (the CSV header row `PARAMETER,YEAR,JAN,...`). However, within the header block, there is a text line reading `Parameter(s):` listing the downloaded climate variables. Case-insensitive matching found this line instead of the true CSV header, causing `pandas` to try parsing human-readable text as CSV columns — resulting in a `ParserError: Expected 1 fields in line 5, saw 15`.

**Resolution:** Changed the detection logic to search for the exact line `-END HEADER-` and start reading from the immediately following line. This is unambiguous because `-END HEADER-` is a fixed delimiter, not a content line. A fallback was added to scan for `PARAMETER,YEAR` (with the comma) in case the header block is absent in future downloads.

---

### Challenge 10 — AQI City Name "Bengaluru" vs "Bangalore" Mismatch
**Problem:** The India AQI dataset (Kaggle CPCB) uses the official city name `Bengaluru` while the NASA files were named with `bangalore` (the older anglicised spelling). A direct string join on city name would have produced zero matches for this city.

**Resolution:** Implemented a city alias dictionary in `preprocess_environmental.py` that maps both `Bengaluru` and `Bangalore` (case-insensitive) to the canonical name `Bengaluru` before the join. All five cities matched successfully, producing 6 rows (years 2015–2020) per city in the merged output.

---

## Section 6 — Final Processed Dataset Summary

| Output file | Shape | Samples/Rows | Features | Label distribution |
|---|---|---|---|---|
| `genomic/gse37250_processed.csv` | 537 × 5003 | 537 samples | 5000 genes | TB: 195, Control: 175, LTBI: 167 |
| `genomic/gse83456_processed.csv` | 202 × 5003 | 202 samples | 5000 genes | TB: 92, Control: 61, Other: 49 |
| `genomic/gse19435_processed.csv` | 33 × 5003 | 33 samples | 5000 genes | TB: 21, Control: 12 |
| `genomic/genomic_combined.csv` | **605 × 112** | **605 samples** | **112 common genes** | **TB: 308, Non-TB: 297** |
| `genomic/gwas_filtered_snps.csv` | 20 × 11 | 20 SNPs | 11 attributes | Top hit: HLA-DQA1/DQB1, p=3×10⁻²³ |
| `proteomic/proteomic_features.csv` | 500 × 41 | 500 proteins | 41 physico-chemical features | — |
| `environmental/env_features.csv` | 30 × 32 | 30 city-years | 15 climate/AQI features (raw + scaled) | — |

---

## Section 7 — Data Quality Notes

### Label balance
The genomic combined matrix has 308 TB vs 297 Non-TB — a near-perfect 51/49 split. This happened naturally from the data, not from artificial sampling. A balanced dataset is important because an imbalanced classifier tends to predict the majority class almost always; with this data we can train and evaluate the classifier fairly without needing SMOTE or oversampling.

### Biological replication
Three independent cohorts (different countries, institutions, time periods, patient populations) contribute to the combined matrix. When the same 112 genes appear as highly variable across all three cohorts, it provides strong evidence that these genes are genuine TB-responsive markers rather than technical artefacts of any one study.

### Feature scale consistency
All numeric features in the proteomic and environmental matrices are MinMax-scaled. The genomic matrix is Z-score normalised per gene. This ensures that when these matrices are fused in Phase 3, no one modality dominates simply due to scale.

### Environmental data coverage
The environmental matrix covers 5 Indian cities × 6 years (2015–2020), totalling 30 city-year observations. While small as a standalone dataset, it provides city-level environmental risk context that will be joined to patient records by city of origin in the fusion phase.

---

## Section 8 — Git Commit Record

**Commit hash:** `de7716f`  
**Commit message:** "Phase 2 complete: all three modalities preprocessed"  
**Files committed:** 12 files:
- 4 preprocessing scripts
- 6 processed CSV outputs
- 1 GPL10558 annotation file (432 MB, tracked by Git LFS)
- 1 `.gitkeep` removal (directories now populated)

**Branch:** `main`  
**Tracking:** GPL10558_family.soft.gz is stored via Git LFS (large file storage); teammates must run `git lfs pull` after cloning to retrieve this file.

---

## Section 9 — What Phase 3 Will Do

Phase 3 is **Multi-Omics Data Fusion** — combining the three processed feature matrices into a single per-patient feature vector. The plan:

1. **Patient-level alignment:** Each patient in the genomic combined matrix has 112 gene expression features. Environmental features (city-year level) will be joined by patient's city of origin and year of sample collection
2. **Proteomic features** (pathogen protein properties) are patient-agnostic — they describe the bacterium, not the host. They will be incorporated as a fixed-length context vector (global feature) in the model architecture rather than a per-patient vector
3. **GWAS SNP features** will be used as prior knowledge to build a biological knowledge graph for the graph neural network component (Phase 5)
4. **Dimensionality reduction:** After fusion, PCA or autoencoder-based reduction will compress the merged feature space before passing it to the main classifier

The unified feature matrix produced in Phase 3 is what gets fed into the Transformer encoder and quantum feature selection layers in Phases 4–6.
