"""
download_datasets.py
====================
Downloads all remaining raw dataset files for the Multi-Omics TB project.

Handles:
  - GPL6947 Illumina annotation  →  data/raw/genomic/
  - UniProt H37Rv FASTA + TSV    →  data/raw/proteomic/
  - PDB structures (KatG, InhA, Rv3804c / FbpA)  →  data/raw/proteomic/structures/
  - WHO TB incidence CSV          →  data/raw/environmental/
  - NASA POWER weather CSV        →  data/raw/environmental/

Kaggle AQI dataset must be downloaded manually (see printed instructions).

Usage:
    python scripts/download_datasets.py
"""

import pathlib
import requests
import time

# ── Base paths ────────────────────────────────────────────────
BASE         = pathlib.Path(__file__).resolve().parent.parent
GENOMIC      = BASE / "data" / "raw" / "genomic"
PROTEOMIC    = BASE / "data" / "raw" / "proteomic"
STRUCTURES   = PROTEOMIC / "structures"
ENVIRON      = BASE / "data" / "raw" / "environmental"

for d in [GENOMIC, PROTEOMIC, STRUCTURES, ENVIRON]:
    d.mkdir(parents=True, exist_ok=True)

# ── Colour helpers ────────────────────────────────────────────
GREEN  = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"; RESET = "\033[0m"
OK   = f"{GREEN}✔{RESET}"
FAIL = f"{RED}✘{RESET}"
SKIP = f"{YELLOW}↷{RESET}"


def download(url: str, dest: pathlib.Path, label: str, chunk_size: int = 65536) -> bool:
    """Downloads url → dest. Skips if file already exists and is non-empty."""
    if dest.exists() and dest.stat().st_size > 1024:
        print(f"  {SKIP}  {label} — already exists, skipping")
        return True
    print(f"  Downloading {label} …", end=" ", flush=True)
    try:
        r = requests.get(url, stream=True, timeout=120,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                f.write(chunk)
        size_kb = dest.stat().st_size // 1024
        print(f"{OK}  ({size_kb:,} KB)")
        return True
    except Exception as exc:
        print(f"{FAIL}  {exc}")
        if dest.exists():
            dest.unlink()
        return False


# ═════════════════════════════════════════════════════════════
# 1. GPL6947 — Illumina HumanHT-12 V4 annotation
#    Needed to convert ILMN_... probe IDs in GEO files to gene names.
# ═════════════════════════════════════════════════════════════
def download_gpl6947():
    print("\n[1/5] GPL6947 Illumina Annotation")
    # NCBI GEO soft file (tab-delimited, contains probe→gene mapping)
    url  = "https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPL6nnn/GPL6947/soft/GPL6947_family.soft.gz"
    dest = GENOMIC / "GPL6947_family.soft.gz"
    ok = download(url, dest, "GPL6947_family.soft.gz")
    if ok:
        print(f"     Note: file is gzip-compressed SOFT format.")
        print(f"     The preprocessing notebook will parse it directly.")


# ═════════════════════════════════════════════════════════════
# 2. UniProt — Mycobacterium tuberculosis H37Rv reviewed proteins
#    REST API returns FASTA and TSV with physicochemical fields.
# ═════════════════════════════════════════════════════════════
def download_uniprot():
    print("\n[2/5] UniProt H37Rv Proteins")

    base_url = "https://rest.uniprot.org/uniprotkb/search"
    query    = "organism_id:83332 AND reviewed:true"   # H37Rv, Swiss-Prot only

    # -- FASTA --
    fasta_dest = PROTEOMIC / "uniprot_h37rv_sequences.fasta"
    fasta_url  = (
        f"{base_url}"
        f"?query={requests.utils.quote(query)}"
        f"&format=fasta"
        f"&size=500"
    )
    download(fasta_url, fasta_dest, "uniprot_h37rv_sequences.fasta")

    # -- TSV with metadata columns (physicochemical props computed later by Biopython) --
    tsv_dest = PROTEOMIC / "uniprot_h37rv_features.tsv"
    fields   = "accession,protein_name,gene_names,organism_name,length,mass," \
               "sequence,cc_subcellular_location,cc_function"
    tsv_url  = (
        f"{base_url}"
        f"?query={requests.utils.quote(query)}"
        f"&format=tsv"
        f"&fields={requests.utils.quote(fields)}"
        f"&size=500"
    )
    download(tsv_url, tsv_dest, "uniprot_h37rv_features.tsv")


# ═════════════════════════════════════════════════════════════
# 3. PDB structures — key TB virulence / drug-target proteins
# ═════════════════════════════════════════════════════════════
PDB_TARGETS = {
    "KatG.pdb"   : "2CCA",   # Catalase-peroxidase — isoniazid resistance marker
    "InhA.pdb"   : "1ENY",   # Enoyl-ACP reductase — primary INH drug target
    "Rv3804c.pdb": "1SFR",   # FbpA / Ag85A — fibronectin attachment, virulence
}

def download_pdb_structures():
    print("\n[3/5] PDB Structure Files")
    for filename, pdb_id in PDB_TARGETS.items():
        url  = f"https://files.rcsb.org/download/{pdb_id}.pdb"
        dest = STRUCTURES / filename
        download(url, dest, f"{filename}  (PDB {pdb_id})")
        time.sleep(0.5)   # be polite to RCSB


# ═════════════════════════════════════════════════════════════
# 4. WHO Global TB Burden data
# ═════════════════════════════════════════════════════════════
def download_who_tb():
    print("\n[4/5] WHO TB Incidence Data")
    # WHO publishes a direct CSV export of TB burden estimates
    url  = "https://extranet.who.int/tme/generateCSV.asp?ds=notifications"
    dest = ENVIRON / "who_tb_incidence.csv"
    ok = download(url, dest, "who_tb_incidence.csv")
    if not ok:
        # Fallback: static annual estimates file
        url2 = "https://extranet.who.int/tme/generateCSV.asp?ds=estimates"
        download(url2, ENVIRON / "who_tb_estimates.csv", "who_tb_estimates.csv (fallback)")


# ═════════════════════════════════════════════════════════════
# 5. NASA POWER — Temperature & Humidity for major Indian cities
#    Uses the NASA POWER API (no account needed).
# ═════════════════════════════════════════════════════════════
INDIAN_CITIES = {
    "Delhi"    : (28.6139,  77.2090),
    "Mumbai"   : (19.0760,  72.8777),
    "Patna"    : (25.5941,  85.1376),
    "Bangalore": (12.9716,  77.5946),
    "Chennai"  : (13.0827,  80.2707),
}

def download_nasa_weather():
    print("\n[5/5] NASA POWER Weather Data")

    import json
    import pandas as pd

    # NASA POWER v2 API — JSON format is most reliable for annual point queries
    nasa_base = "https://power.larc.nasa.gov/api/temporal/annual/point"

    all_rows = []

    for city, (lat, lon) in INDIAN_CITIES.items():
        print(f"  Fetching {city} …", end=" ", flush=True)
        params = {
            "parameters" : "T2M,RH2M",
            "community"  : "RE",      # Renewable Energy community — broadest dataset
            "longitude"  : lon,
            "latitude"   : lat,
            "start"      : 2015,
            "end"        : 2020,
            "format"     : "JSON",
        }
        try:
            r = requests.get(nasa_base, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()

            # Navigate NASA POWER JSON structure
            properties = data.get("properties", {}).get("parameter", {})
            t2m  = properties.get("T2M",  {})
            rh2m = properties.get("RH2M", {})

            for year_key in t2m:
                all_rows.append({
                    "city"        : city,
                    "year"        : int(year_key),
                    "temperature" : t2m[year_key],
                    "humidity"    : rh2m.get(year_key, None),
                    "latitude"    : lat,
                    "longitude"   : lon,
                })

            print(f"{OK}  ({len(t2m)} years)")
        except Exception as exc:
            print(f"{FAIL}  {exc}")
        time.sleep(1)

    if all_rows:
        df = pd.DataFrame(all_rows)
        dest = ENVIRON / "nasa_weather.csv"
        df.to_csv(dest, index=False)
        print(f"  Saved → {dest}  ({len(df)} rows)")
    else:
        print(f"  {FAIL} No weather data retrieved — check internet connection.")


# ═════════════════════════════════════════════════════════════
# MANUAL STEP — Kaggle India AQI (requires Kaggle login)
# ═════════════════════════════════════════════════════════════
def print_kaggle_instructions():
    print(f"""
{'═'*60}
  MANUAL DOWNLOAD REQUIRED — Kaggle India AQI Dataset
{'═'*60}

  1. Go to: https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india
  2. Sign in to Kaggle (free account)
  3. Click the  Download  button (downloads a .zip)
  4. Extract the zip — look for "city_day.csv"  (best file to use)
  5. Rename it to  india_aqi.csv
  6. Move it to:
       {ENVIRON}

  Columns you need: City, Date, PM2.5, PM10, NO2, AQI
  Date range: 2015–2020

{'═'*60}
""")


# ═════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Multi-Omics TB — Dataset Downloader")
    print("=" * 60)

    download_gpl6947()
    download_uniprot()
    download_pdb_structures()
    download_who_tb()
    download_nasa_weather()
    print_kaggle_instructions()

    print("\nAll automated downloads complete.")
    print("Once you have placed india_aqi.csv in data/raw/environmental/,")
    print("all datasets will be ready for preprocessing.\n")
