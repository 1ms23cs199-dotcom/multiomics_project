# Project Progress Log
## Quantum-AI Powered Multi-Omics Disease Insight Engine
**Institution:** M.S. Ramaiah Institute of Technology, Bangalore
**Target Disease:** Tuberculosis (TB)
**Log started:** February 28, 2026

---

## Phase 0 — Environment Setup ✅ Complete

### What was done
- Installed Python 3.11 and created a virtual environment (`venv`) inside the project folder
- Installed core bioinformatics and data science libraries:
  ```
  biopython, pandas, numpy, scipy, scikit-learn, matplotlib, seaborn, requests
  ```
- Established the project folder structure across all three data modalities:
  ```
  data/raw/genomic/
  data/raw/proteomic/structures/
  data/raw/environmental/
  data/processed/genomic|proteomic|environmental/
  models/ | api/ | vr/ | dashboard/ | scripts/ | notebooks/
  ```
- Verified the environment with `python -c "import pandas; import numpy; import Bio; print('All good')"` — passed successfully

### Challenges
None significant. Standard setup.

---

## Phase 1 — Data Acquisition ✅ Complete

### What was done
Systematically identified and acquired 18 raw dataset files across three biological modalities and wrote a reusable automated download script (`scripts/download_datasets.py`).

**Genomic (6 files)** — downloaded manually from NCBI GEO and GWAS Catalog:
- GSE37250, GSE19435, GSE83456 series matrix files (GEO microarray datasets)
- GPL6947 Illumina probe annotation file
- GWAS Catalog TB-associated SNP file
- H37Rv reference genome FASTA (NC_000962.3)

**Proteomic (5 files)** — downloaded via automated script using UniProt REST API and RCSB PDB:
- UniProt H37Rv protein sequences (FASTA format)
- UniProt H37Rv metadata (TSV format)
- 3D protein structures: KatG, InhA, Rv3804c (PDB format)

**Environmental (7 files)** — mixed automated and manual:
- WHO TB incidence CSV — automated via WHO data portal
- India AQI dataset — manually downloaded from Kaggle
- NASA POWER weather data (5 city files) — browser URL method

### Challenges Faced and How They Were Resolved

---

#### Challenge 1 — UniProt TSV Download Returning HTTP 400 Error
**Problem:** The initial automated download script used field names (`cc_instability`, `isoelectric_point`, `ft_regions`) that are not valid in the current UniProt REST API v2. The API returned a 400 Bad Request error and no file was saved.

**What we tried first:** Checked if the URL was malformed — it was structurally correct but the field parameter names had changed in a recent UniProt API update.

**Resolution:** Replaced the invalid field names with valid v2 API fields (`cc_subcellular_location`, `cc_function`). The physicochemical values (isoelectric point, instability index) that were unavailable via API are instead computed directly from the FASTA sequences using Biopython's `ProteinAnalysis` module during preprocessing — a more reliable approach that doesn't depend on external API field availability.

**Skill demonstrated:** API debugging, reading HTTP error codes, adapting to breaking API changes, finding an equivalent programmatic solution.

---

#### Challenge 2 — NASA POWER API Returning HTTP 404 Errors
**Problem:** The automated download script called the NASA POWER annual point API with `community=AG` (Agroclimatology) and CSV format. The endpoint returned 404 Not Found for all five cities, producing no weather data.

**What we tried first:** Verified internet connectivity — other downloads worked fine, so the issue was specific to the NASA endpoint. Tested with `community=RE` (Renewable Energy) and JSON format — still failed programmatically due to URL parameter encoding issues.

**Resolution:** Switched to a direct browser URL method using `%2C` (URL-encoded comma) to correctly pass both parameters (`T2M%2CRH2M`) simultaneously. Pasting the constructed URLs directly into a browser triggered correct CSV downloads for all five cities (Delhi, Mumbai, Patna, Bangalore, Chennai). Files were manually saved and named consistently (`nasa_delhi.csv` etc.).

**Skill demonstrated:** URL encoding knowledge, switching between programmatic and manual approaches pragmatically, browser-based API access as a fallback.

---

#### Challenge 3 — NASA POWER Data Access Tool Showing a Regional Map
**Problem:** When navigating to the NASA POWER Data Access Viewer website, the interface defaulted to a regional bounding box mode (requiring upper-left and lower-right lat/lon corners) rather than the single-point mode needed for city-level data.

**Resolution:** Bypassed the map interface entirely by constructing direct API URLs with exact latitude and longitude coordinates for each city. This was faster and more reproducible than using the GUI.

**Skill demonstrated:** Recognising when a GUI tool is not the right approach and switching to API-level interaction.

---

#### Challenge 4 — NASA POWER Only Downloading One Parameter at a Time
**Problem:** Initial browser URL attempts with `parameters=T2M,RH2M` (comma-separated) only returned temperature data — the comma was being interpreted as a URL delimiter, silently dropping the second parameter.

**Resolution:** Replaced the plain comma with its URL-encoded equivalent `%2C`, giving `parameters=T2M%2CRH2M`. The resulting CSV correctly contained both the T2M (temperature) and RH2M (humidity) columns.

**Skill demonstrated:** Understanding URL encoding, debugging silent data loss in API responses.

---

#### Challenge 5 — `requests` Library Not Found in Virtual Environment
**Problem:** Running `download_datasets.py` initially threw `ModuleNotFoundError: No module named 'requests'` even though the virtual environment appeared active.

**Resolution:** Installed `requests` and `pandas` explicitly into the virtual environment using the full path to the venv Python interpreter:
```
C:/Users/trish/multiomics_project/venv/Scripts/python.exe -m pip install requests pandas
```
This ensures packages install into the correct environment rather than system Python.

**Skill demonstrated:** Virtual environment management, using the full interpreter path to avoid environment confusion.

---

### Final Dataset Inventory
All 18 files confirmed present and non-empty as of February 28, 2026:

| Modality | Files | Total Size |
|----------|-------|-----------|
| Genomic | 6 files | ~258 MB |
| Proteomic | 5 files | ~2.7 MB |
| Environmental | 7 files | ~5.5 MB |
| **Total** | **18 files** | **~266 MB** |

---

## Phase 2 — Preprocessing 🔜 Next

Planned steps:
1. Parse GPL6947 SOFT file → build probe ID → gene name mapping table
2. Extract expression matrix and TB/healthy labels from GSE37250
3. Process GSE19435 and GSE83456 using the same pipeline
4. Filter GWAS SNPs by p-value threshold (< 5×10⁻⁶)
5. Compute physicochemical features from UniProt FASTA using Biopython
6. Merge 5 NASA city CSVs and join with India AQI data on city + year

Expected output: clean feature matrices in `data/processed/` for each modality.

---

*This log is updated at the end of each completed phase.*
