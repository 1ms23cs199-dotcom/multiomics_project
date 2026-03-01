# Dataset Registry — Quantum-AI Multi-Omics TB Insight Engine
**M.S. Ramaiah Institute of Technology | 6th Semester CSE**  
**Last verified:** February 28, 2026  
**Status: ALL DATASETS PRESENT ✅**

---

## Overall Data Architecture

This project integrates three independent biological and environmental data streams into one unified model. The diagram below shows how each dataset feeds into the pipeline:

```
GENOMIC DATA                PROTEOMIC DATA              ENVIRONMENTAL DATA
──────────────              ──────────────              ──────────────────
GSE37250 (train)            UniProt FASTA               India AQI CSV
GSE19435 (validate)    →    UniProt TSV            →    NASA Weather CSVs
GSE83456 (supplement)       KatG / InhA / Rv3804c       WHO TB Incidence
GPL6947  (annotation)
GWAS SNPs
sequence.fasta
       ↓                           ↓                           ↓
  Gene Expression            Physicochemical              Environmental
  Feature Vector             Feature Vector               Feature Vector
       ↓                           ↓                           ↓
       └───────────── FUSION MODEL ─────────────────────────┘
                              ↓
                    Quantum Feature Selection
                              ↓
                      TB Risk Score Output
```

---

## SECTION 1 — GENOMIC DATASETS

### 1. GSE37250 — Primary Training Dataset
**File:** `genomic/GSE37250_series_matrix.txt.gz`  
**Size:** 103 MB (compressed) | **Source:** NCBI GEO  
**Status:** ✅ Downloaded

#### What it is
A gene expression microarray dataset generated from whole blood samples of human patients. It was produced using the Illumina HumanHT-12 v4 BeadChip platform, which simultaneously measures the activity level of approximately 47,000 probes (each representing a region of a gene) across multiple patient samples.

#### Biological significance
When *Mycobacterium tuberculosis* infects a human, it triggers a cascade of immune responses. Genes encoding cytokines (like TNF-α, IFN-γ, IL-6), pattern recognition receptors (like TLR2, TLR4), and antimicrobial peptides become upregulated — meaning the host is actively trying to destroy the pathogen. At the same time, the bacterium subverts normal macrophage function, so genes controlling phagosome maturation and autophagy get disrupted. This dataset captures exactly these signatures — the molecular fingerprint of TB infection in the human immune system.

#### Contribution to the project
- **536 samples** with labels: active TB, latent TB, healthy controls, and other lung diseases
- Primary source of **gene expression feature vectors** (input to the Transformer encoder)
- Labels extracted from metadata headers are used as **ground-truth training targets**
- Largest and most cited GEO dataset for TB expression — gives the model the strongest signal

---

### 2. GSE19435 — Cross-Dataset Validation Set
**File:** `genomic/GSE19435_series_matrix.txt.gz`  
**Size:** 7 MB (compressed) | **Source:** NCBI GEO  
**Status:** ✅ Downloaded

#### What it is
A second independent microarray gene expression dataset from blood samples of TB patients and healthy controls, collected under a different study and at a different institution than GSE37250.

#### Biological significance
TB disease manifests differently in patients depending on host genetics, immune status, age, and geographic origin. Using a dataset from a completely independent cohort tests whether the gene expression signatures learned by the model are universal markers of TB biology rather than study-specific artefacts. Key biomarkers validated across both datasets — such as elevated expression of **GBP1**, **IFIT1**, **STAT1** (interferon-stimulated genes) — are considered robust biological signals of TB infection.

#### Contribution to the project
- Used exclusively as a **held-out validation set** — the model never trains on this data
- Tests **cross-cohort generalisation** — the most rigorous form of model evaluation for clinical datasets
- ~150 samples

---

### 3. GSE83456 — Supplementary Training Data
**File:** `genomic/GSE83456_series_matrix.txt.gz`  
**Size:** 34 MB (compressed) | **Source:** NCBI GEO  
**Status:** ✅ Downloaded

#### What it is
A third gene expression dataset with ~200 samples covering TB patients and controls. Population origin requires metadata verification before use.

#### Biological significance
Adds diversity to the training cohort. Different populations (South Asian, African, European) have different frequencies of immune-related genetic variants — for example, variants in the **SLC11A1** gene (which encodes a transporter critical for macrophage resistance to mycobacteria) vary significantly across ethnicities. A more diverse training set reduces bias and makes the final model more clinically applicable to Indian TB patients.

#### Contribution to the project
- Merged with GSE37250 to increase total training sample size
- Population metadata used to check Indian cohort relevance
- Improves model robustness against demographic variation

---

### 4. GPL6947 — Illumina Probe Annotation File
**File:** `genomic/GPL6947_family.soft.gz`  
**Size:** 108 MB (compressed) | **Source:** NCBI GEO  
**Status:** ✅ Downloaded

#### What it is
A mapping table that translates Illumina microarray probe identifiers (e.g., `ILMN_1343048`) into human gene names (e.g., `GAPDH`, `TP53`, `STAT1`). The GEO series matrix files (GSE37250 etc.) contain probe IDs, not gene names — this file is the dictionary that converts them.

#### Biological significance
Without this file, the gene expression data consists of meaningless numeric IDs. This annotation enables:
- Identification of which biological pathways are active in TB patients
- Feature labelling for model interpretability (clinicians need to know *which genes* drive predictions, not just probe IDs)
- Cross-referencing with published TB biomarker lists (e.g., the 3-gene signature: **GBP5**, **DUSP3**, **KLF2**)

#### Contribution to the project
- **Essential preprocessing dependency** — must be applied before any downstream analysis
- Maps ~47,000 probe IDs to ~20,000 unique genes
- Enables the final feature importance output to name actual genes, not probe codes

---

### 5. GWAS SNP File — TB-Associated Genetic Variants
**File:** `genomic/gwas-association-downloaded_2026-02-28-EFO_1000049.tsv`  
**Size:** 20 KB | **Source:** GWAS Catalog (trait: pulmonary tuberculosis)  
**Status:** ✅ Downloaded

#### What it is
Results from published Genome-Wide Association Studies (GWAS) for tuberculosis. Each row represents a Single Nucleotide Polymorphism (SNP) — a single DNA base-pair change at a specific genomic location — that has been statistically associated with TB susceptibility or resistance in a population-level study.

#### Biological significance
Most TB susceptibility research has focused on the pathogen, but the host genome matters enormously. The following SNPs have documented biological roles in TB:

| SNP | Gene | Biological Role |
|-----|------|-----------------|
| rs17235409 | SLC11A1 | Controls iron transport in macrophages; variants impair mycobacterial killing |
| rs4331426 | ASAP1 | Affects dendritic cell migration and antigen presentation efficiency |
| rs2057178 | Chr18q11 | Near JAK2; affects cytokine signalling strength |

These variants explain why in TB-endemic regions, some individuals exposed to the bacterium never develop disease while others progress rapidly.

#### Contribution to the project  
- Filtered to significant hits (p < 5×10⁻⁶) to extract **candidate SNP features**
- SNP flags encoded as binary features in the genomic feature vector
- Used in feature importance output to flag high-risk variants in the API response (`"top_features": [{"feature": "SNP_rs17235409", ...}]`)

---

### 6. sequence.fasta — TB Pathogen Reference Genome
**File:** `genomic/sequence.fasta`  
**Size:** 4.4 MB | **Source:** NCBI (H37Rv strain, NC_000962.3)  
**Status:** ✅ Downloaded

#### What it is
The complete 4.4 million base-pair genome of *Mycobacterium tuberculosis* H37Rv — the universal reference strain used in all TB research worldwide. It is stored in FASTA format, a plain-text representation of a DNA sequence.

#### Biological significance
H37Rv is the best-characterised TB strain in existence, with every gene annotated and its function experimentally verified. The genome encodes:
- **4,111 genes**, including drug resistance genes (katG, rpoB, inhA)
- **PE/PPE gene families** (~170 genes) — highly variable surface proteins that help the bacterium evade immune detection
- **Regulatory regions** that control virulence factor expression in response to environmental stress

The genome sequence is the foundation for k-mer frequency analysis, where the DNA is broken into overlapping substrings of length k and their frequencies counted — a numeric representation that captures sequence composition without requiring alignment.

#### Contribution to the project
- Source for **k-mer feature extraction** (sequence-level genomic feature vector)
- Reference for mapping variant positions from GWAS SNPs
- PDB structure files for virulence proteins are encoded from genes in this genome
- Used by Biopython's `SeqIO` module for parsing

---

## SECTION 2 — PROTEOMIC DATASETS

### 7. UniProt H37Rv Protein Sequences (FASTA)
**File:** `proteomic/uniprot_h37rv_sequences.fasta`  
**Size:** 288 KB | **Source:** UniProt (Swiss-Prot, reviewed)  
**Status:** ✅ Downloaded

#### What it is
Amino acid sequences for all proteins encoded by *M. tuberculosis* H37Rv that have been **experimentally reviewed** and deposited in the Swiss-Prot section of UniProt. Each entry represents a protein whose function is known.

#### Biological significance
Proteins are the ultimate executors of the instructions encoded in DNA. In TB:
- **Virulence proteins** (like FbpA/Rv3804c) allow the bacterium to bind human lung tissue
- **Drug target proteins** (like InhA) are the molecules that TB medicines are designed to block 
- **Drug resistance proteins** (like KatG) become mutated in drug-resistant TB strains, making first-line antibiotics ineffective

The amino acid sequence of a protein directly determines its 3D structure, and its 3D structure determines its function. Physicochemical properties computed from the sequence (isoelectric point, instability index, hydrophobicity) give the ML model quantifiable signals about protein behaviour.

#### Contribution to the project
- Biopython's `ProteinAnalysis` module reads these sequences and computes **26 physicochemical features per protein** (amino acid composition, molecular weight, pI, GRAVY, instability index, secondary structure fractions)
- These form the **proteomic feature vector** input to the fusion model
- Also parsed by Biopython `SeqIO` for k-mer encoding at the protein level

---

### 8. UniProt H37Rv Feature Metadata (TSV)
**File:** `proteomic/uniprot_h37rv_features.tsv`  
**Size:** 667 KB | **Source:** UniProt REST API  
**Status:** ✅ Downloaded

#### What it is
A tabular metadata file with columns including: UniProt accession, protein name, gene name, organism, sequence length, mass, subcellular location, and functional annotation for each H37Rv protein.

#### Biological significance
Subcellular location is biologically critical for TB. Proteins located in:
- **Cell wall** → directly interact with host immune cells and antibiotics
- **Cytoplasm** → involved in metabolic pathways targeted by drug combinations
- **Secreted** → released into host cells to manipulate immune signalling

Knowing where a protein is located helps explain the biological plausibility of risk predictions.

#### Contribution to the project
- Merged with the FASTA-derived features to create the complete proteomic feature matrix
- Gene names allow cross-referencing with the genomic data (same gene, both DNA and protein level)
- Protein mass and length used as normalisation-invariant baseline features
- Subcellular location can be one-hot encoded as a categorical feature

---

### 9. KatG.pdb — Catalase-Peroxidase Structure
**File:** `proteomic/structures/KatG.pdb`  
**Size:** 1 MB | **PDB ID:** 2CCA | **Source:** RCSB PDB  
**Status:** ✅ Downloaded

#### What it is
The experimentally determined 3D atomic structure of KatG, the catalase-peroxidase enzyme of *M. tuberculosis*, resolved by X-ray crystallography. Every atom in the protein is assigned xyz coordinates.

#### Biological significance
KatG is one of the most clinically important proteins in all of TB medicine. Its role:
1. **Normal function** — KatG activates isoniazid (INH), the most widely used first-line TB antibiotic, by converting it to its active toxic form inside the bacterium
2. **Resistance mechanism** — when the katG gene mutates (most commonly at position S315T), KatG can no longer activate isoniazid, causing **isoniazid-resistant TB** (found in ~17% of new TB cases globally)
3. **Drug resistance marker** — KatG mutation status is used clinically to determine which antibiotics to prescribe

In the VR module, mutation sites on KatG are highlighted in red when the AI predicts high drug-resistance risk.

#### Contribution to the project
- Loaded in **Unity 3D** using a PDB file importer
- Residue positions from GWAS/variant data used to highlight mutation hotspots on the 3D structure
- Risk score ≥ 0.7 triggers `glow_red` animation effect on mutated residues
- Gives the VR module clinical interpretability — students can see *exactly where* INH resistance occurs on the protein

---

### 10. InhA.pdb — Enoyl-ACP Reductase Structure
**File:** `proteomic/structures/InhA.pdb`  
**Size:** 200 KB | **PDB ID:** 1ENY | **Source:** RCSB PDB  
**Status:** ✅ Downloaded

#### What it is
The 3D crystal structure of InhA, the enoyl-acyl carrier protein reductase enzyme of *M. tuberculosis*.

#### Biological significance
InhA is the **primary molecular target** of isoniazid — once KatG activates INH, the active form binds directly to InhA and blocks it. InhA is essential for synthesising mycolic acids — the long fatty acid chains that form the waxy cell wall of *M. tuberculosis*. Without a functional cell wall, the bacterium dies. InhA mutations (e.g., I21V, S94A) reduce isoniazid binding affinity, conferring resistance even when KatG is intact.

#### Contribution to the project
- Second protein structure for the VR interactive viewer
- Demonstrates the **drug target pathway** visually: students can see the active site where INH binds
- Complementary to KatG — together they show both sides of the isoniazid resistance mechanism
- Protein stability score from the AI model drives the `protein_stability: "unstable"` signal in the API output

---

### 11. Rv3804c.pdb — FbpA / Antigen 85A Structure
**File:** `proteomic/structures/Rv3804c.pdb`  
**Size:** 568 KB | **PDB ID:** 1SFR | **Source:** RCSB PDB  
**Status:** ✅ Downloaded

#### What it is
The 3D structure of Rv3804c (also called FbpA or Antigen 85A), a secreted fibronectin-binding protein of *M. tuberculosis*.

#### Biological significance
Rv3804c is central to TB virulence and infection:
1. **Cell wall synthesis** — FbpA transfers mycolic acids onto arabinogalactan to build the bacterial cell wall, making it essential for survival
2. **Host attachment** — the protein binds fibronectin on human lung alveolar cells, allowing TB to physically anchor itself to lung tissue before macrophage uptake
3. **Vaccine candidate** — Ag85A is one of the most intensively studied TB vaccine antigens; it is a component of several experimental vaccines in clinical trials
4. **Diagnostic relevance** — Ag85A is detectable in patient sputum and blood, providing a potential biomarker for early TB diagnosis

#### Contribution to the project
- Third interactive structure in the VR module — gives a view of TB from the **virulence and host-interaction angle**, not just drug resistance
- Shows students the physical mechanism by which TB infects lung cells
- Future expansion: can use the fibronectin-binding site to demonstrate drug discovery concepts

---

## SECTION 3 — ENVIRONMENTAL DATASETS

### 12. India AQI Dataset
**File:** `environmental/india_aqi.csv`  
**Size:** 2.5 MB | **Source:** Kaggle (rohanrao)  
**Status:** ✅ Downloaded

#### What it is
Daily air quality measurements from monitoring stations across major Indian cities from 2015 to 2020. Columns include: City, Date, PM2.5, PM10, NO2, SO2, CO, O3, and AQI (Air Quality Index).

#### Biological significance
Air pollution and TB are deeply connected at the biological level:
- **PM2.5 (fine particles < 2.5µm)** — particles this small penetrate deep into the alveoli, the air sacs where TB infection begins. They cause sustained inflammation, impair mucociliary clearance (the lung's self-cleaning mechanism), and suppress alveolar macrophage function — the very immune cells responsible for killing *M. tuberculosis*
- **PM10** — larger particles damage the upper respiratory tract, increasing vulnerability to initial bacterial entry
- **NO2 (Nitrogen Dioxide)** — produced by vehicle exhaust; impairs neutrophil and macrophage function, reducing the immune system's ability to contain early TB infection
- **AQI** — composite measure; epidemiological studies show cities with chronic AQI > 150 have TB incidence rates 2–3× higher than cities with AQI < 50

India has 26% of the world's TB burden. Cities like Delhi (annual average PM2.5 ~90 µg/m³, far above the WHO limit of 5 µg/m³) are simultaneously among the world's most polluted and most TB-affected.

#### Contribution to the project
- Provides 4 of the 7 environmental features in the model: **PM2.5, PM10, NO2, AQI**
- Merged with NASA weather data on `city + year` keys to form the complete environmental feature vector
- Enables city-level risk prediction — a public health worker can input their city name and get an environment-driven TB risk estimate
- Post-deployment: AQI slider in the VR module connects directly to values from this dataset

---

### 13. NASA POWER Weather Data (5 city files)
**Files:** `environmental/nasa_delhi.csv`, `nasa_mumbai.csv`, `nasa_patna.csv`, `nasa_bangalore.csv`, `nasa_chennai.csv`  
**Size:** 1.6 KB each | **Source:** NASA POWER API (RE community)  
**Status:** ✅ Downloaded

#### What it is
Annual averages of two atmospheric parameters for five major Indian cities, sourced from NASA's Prediction of Worldwide Energy Resources (POWER) project — a satellite-derived dataset that provides consistent, gap-free climate data.

Parameters:
- **T2M** — Air temperature at 2 metres above ground level (°C)
- **RH2M** — Relative humidity at 2 metres above ground level (%)

#### Biological significance
Temperature and humidity have direct effects on TB transmission and severity:

**Temperature:**
- *M. tuberculosis* survives in aerosol droplets for longer at moderate temperatures (15–25°C)
- Cold winters in North Indian cities (Patna, Delhi) drive people indoors into poorly ventilated spaces, dramatically increasing transmission probability
- High temperatures above 37°C reduce bacterial survival in expelled droplets

**Humidity:**
- Low humidity (dry air) in winter extends the viability of TB-containing aerosol particles suspended in air — they remain infectious for hours rather than minutes
- High humidity reduces aerosol survival but increases mould co-infections that can mimic or worsen TB symptoms
- The hygroscopic nature of the M. tuberculosis cell wall (due to mycolic acids) means its survival outside a host is humidity-dependent

India's monsoon season (June–September) sees a temporary drop in airborne TB transmission due to high humidity and rainfall settling dust and droplets, while the post-monsoon dry season sees a resurgence.

#### Contribution to the project
- Provides 2 of the 7 environmental features: **temperature, humidity**
- Merged with AQI data to complete the environmental feature vector
- Year-wise data (2015–2020) aligns with the AQI dataset date range
- Enables the model to account for seasonal/climatic variation in TB risk

---

### 14. WHO TB Incidence Data
**File:** `environmental/who_tb_incidence.csv`  
**Size:** 2.9 MB | **Source:** WHO Global TB Programme  
**Status:** ✅ Downloaded

#### What it is
The WHO's official annual TB surveillance data covering every country in the world. Contains estimated TB incidence rates, prevalence, mortality, treatment success rates, drug-resistant TB burden, and HIV-TB co-infection rates from 2000 to the most recent reporting year.

#### Biological significance
This dataset contextualises the molecular-level findings within the actual population-level disease burden. Key metrics:
- **Incidence rate** (new TB cases per 100,000 people per year) — India's rate (~210 per 100,000) is among the highest globally
- **MDR-TB (Multi-Drug Resistant TB) proportion** — the fraction of TB cases resistant to at least rifampicin and isoniazid, the two most important first-line drugs; directly relates to KatG and InhA protein mutations captured in the proteomic data
- **HIV-TB co-infection rate** — HIV severely depletes CD4+ T cells, which are critical for containing TB infection; the immune gene expression signatures in GEO datasets look very different in HIV+ vs HIV- TB patients

#### Contribution to the project
- Provides **population-level disease labels** to calibrate the model's risk scores against real-world incidence
- MDR-TB rates link back to the drug resistance protein structures (KatG, InhA)
- Can be used to weight training samples by national TB burden for fairer model training
- Powers the policy-maker use case: a health official can see their city's predicted risk score plotted against WHO-reported national trends on the Streamlit dashboard

---

## Summary Table — All Datasets

| # | File | Folder | Size | Status | Phase Used |
|---|------|--------|------|--------|-----------|
| 1 | GSE37250_series_matrix.txt.gz | genomic | 103 MB | ✅ | Phase 2, 3, 4 |
| 2 | GSE19435_series_matrix.txt.gz | genomic | 7 MB | ✅ | Phase 2, 8 |
| 3 | GSE83456_series_matrix.txt.gz | genomic | 34 MB | ✅ | Phase 2, 4 |
| 4 | GPL6947_family.soft.gz | genomic | 108 MB | ✅ | Phase 2 |
| 5 | gwas-association-downloaded...tsv | genomic | 20 KB | ✅ | Phase 2, 3 |
| 6 | sequence.fasta | genomic | 4.4 MB | ✅ | Phase 3 |
| 7 | uniprot_h37rv_sequences.fasta | proteomic | 288 KB | ✅ | Phase 3 |
| 8 | uniprot_h37rv_features.tsv | proteomic | 667 KB | ✅ | Phase 3 |
| 9 | KatG.pdb | proteomic/structures | 1 MB | ✅ | Phase 10 (VR) |
| 10 | InhA.pdb | proteomic/structures | 200 KB | ✅ | Phase 10 (VR) |
| 11 | Rv3804c.pdb | proteomic/structures | 568 KB | ✅ | Phase 10 (VR) |
| 12 | india_aqi.csv | environmental | 2.5 MB | ✅ | Phase 2, 3, 5 |
| 13 | nasa_delhi.csv | environmental | 1.6 KB | ✅ | Phase 2, 3 |
| 14 | nasa_mumbai.csv | environmental | 1.6 KB | ✅ | Phase 2, 3 |
| 15 | nasa_patna.csv | environmental | 1.6 KB | ✅ | Phase 2, 3 |
| 16 | nasa_bangalore.csv | environmental | 1.6 KB | ✅ | Phase 2, 3 |
| 17 | nasa_chennai.csv | environmental | 1.6 KB | ✅ | Phase 2, 3 |
| 18 | who_tb_incidence.csv | environmental | 2.9 MB | ✅ | Phase 2, 8 |

**Total: 18/18 files present. Data acquisition phase COMPLETE.**

---

---

## Note on the `labels/` Folder

The `data/raw/labels/tb_xray/` folder was created for the **optional TB Chest X-Ray dataset** (Kaggle — tawsifurrahman, 3,500+ images labeled TB / Normal).

**This dataset is NOT required for the current prototype.** Reasons:

- Primary TB/healthy labels are already embedded in the **GSE37250 metadata header** and will be extracted during preprocessing — no separate label file is needed
- The X-ray dataset would only become relevant if a **4th imaging modality** is added to the fusion model (a stretch goal, not a primary objective)
- The project brief explicitly marks it as: *"optional — use only if adding image as 4th modality"*

**Action required: None.** Leave the folder empty. Revisit only if time permits after all primary objectives are complete.

---

## Next Step
Begin **Phase 2 — Preprocessing** when ready:
1. Parse GPL6947 annotation → convert probe IDs to gene names
2. Extract expression matrix and labels from GSE37250
3. Filter GWAS SNPs by p-value threshold
4. Compute proteomic physicochemical features from UniProt FASTA
5. Merge NASA city CSVs and join with AQI data
