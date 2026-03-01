"""
preprocess_environmental.py
============================
Merges five NASA POWER city CSVs (T2M, RH2M) with India AQI data
and optionally WHO TB incidence data into a unified environmental
feature matrix.

Output
------
data/processed/environmental/env_features.csv
    Rows    : one per (city, year)
    Columns : city, year, T2M_mean, RH2M_mean,
              PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3,
              Benzene, Toluene, Xylene, AQI   (+ MinMax-scaled versions)
"""

import re
import glob
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# ── Paths ────────────────────────────────────────────────────────────────────
RAW_ENV   = Path("data/raw/environmental")
OUT_DIR   = Path("data/processed/environmental")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Map filename stem → canonical city name matching india_aqi.csv
CITY_MAP = {
    "nasa_delhi":     "Delhi",
    "nasa_mumbai":    "Mumbai",
    "nasa_patna":     "Patna",
    "nasa_bangalore": "Bengaluru",   # Kaggle AQI uses "Bengaluru"
    "nasa_chennai":   "Chennai",
}

# ── 1. Parse NASA POWER CSVs ─────────────────────────────────────────────────

def parse_nasa_csv(filepath: Path, city_name: str) -> pd.DataFrame:
    """
    NASA POWER CSVs have a variable-length header block:
        -BEGIN HEADER-
        …
        -END HEADER-
        PARAMETER,YEAR,JAN,FEB,…,DEC,ANN
        RH2M,2015,52.03,…
        T2M,2015,12.64,…

    Parameters are ROWS; we pivot them into columns.
    We keep only the ANN (annual mean) column.
    """
    lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()

    # Find the line immediately after "-END HEADER-"
    data_start = None
    for i, line in enumerate(lines):
        if line.strip().upper() == "-END HEADER-":
            data_start = i + 1
            break

    # Fallback: look for the CSV header row "PARAMETER,YEAR,..."
    if data_start is None:
        for i, line in enumerate(lines):
            if line.strip().upper().startswith("PARAMETER,YEAR"):
                data_start = i
                break

    if data_start is None:
        raise ValueError(f"Could not find data section in {filepath}")

    from io import StringIO
    csv_block = "\n".join(lines[data_start:])
    df = pd.read_csv(StringIO(csv_block))

    # Normalise column names
    df.columns = [c.strip() for c in df.columns]

    # Keep only PARAMETER, YEAR, and ANN (annual mean)
    df = df[["PARAMETER", "YEAR", "ANN"]].copy()
    df.rename(columns={"YEAR": "year"}, inplace=True)

    # Pivot: each PARAMETER becomes a column
    df_pivot = df.pivot_table(index="year", columns="PARAMETER", values="ANN")
    df_pivot.reset_index(inplace=True)
    df_pivot.columns.name = None

    # Rename columns to include an indication of the source
    rename = {"RH2M": "RH2M_mean", "T2M": "T2M_mean"}
    df_pivot.rename(columns=rename, inplace=True)

    df_pivot.insert(0, "city", city_name)
    df_pivot["year"] = df_pivot["year"].astype(int)
    return df_pivot


def load_nasa_all() -> pd.DataFrame:
    frames = []
    for stem, city in CITY_MAP.items():
        candidate = RAW_ENV / f"{stem}.csv"
        if not candidate.exists():
            print(f"  [WARN] NASA file not found: {candidate} — skipping")
            continue
        print(f"  Parsing {candidate.name} → {city}")
        frames.append(parse_nasa_csv(candidate, city))

    if not frames:
        raise FileNotFoundError("No NASA POWER CSV files found in " + str(RAW_ENV))
    return pd.concat(frames, ignore_index=True)


# ── 2. Parse India AQI CSV ───────────────────────────────────────────────────

AQI_COLS = ["PM2.5", "PM10", "NO", "NO2", "NOx", "NH3",
            "CO", "SO2", "O3", "Benzene", "Toluene", "Xylene", "AQI"]


def load_aqi() -> pd.DataFrame:
    aqi_path = RAW_ENV / "india_aqi.csv"
    if not aqi_path.exists():
        raise FileNotFoundError(f"AQI file not found: {aqi_path}")

    df = pd.read_csv(aqi_path, parse_dates=["Date"])
    df["year"] = df["Date"].dt.year

    # Standardise city names for the five NASA cities
    city_alias = {
        "Delhi":     ["Delhi"],
        "Mumbai":    ["Mumbai"],
        "Patna":     ["Patna"],
        "Bengaluru": ["Bengaluru", "Bangalore"],
        "Chennai":   ["Chennai"],
    }
    canonical = {}
    for canon, aliases in city_alias.items():
        for a in aliases:
            canonical[a.lower()] = canon

    df["city"] = df["City"].str.strip().str.lower().map(canonical)
    df = df.dropna(subset=["city"])

    # Aggregate: annual mean per city × year
    agg = df.groupby(["city", "year"])[AQI_COLS].mean().reset_index()
    return agg


# ── 3. Optionally load WHO TB incidence ──────────────────────────────────────

def load_who() -> pd.DataFrame | None:
    who_glob = list(RAW_ENV.glob("who_tb_incidence*"))
    if not who_glob:
        print("  [INFO] WHO TB incidence file not found — skipping.")
        return None

    path = who_glob[0]
    df = pd.read_csv(path, encoding="latin-1")
    # Filter to India rows if possible
    country_cols = [c for c in df.columns if "country" in c.lower()]
    if country_cols:
        df = df[df[country_cols[0]].str.lower().str.contains("india", na=False)]

    # Keep year + incidence column (best guess at column name)
    year_cols = [c for c in df.columns if "year" in c.lower()]
    inc_cols  = [c for c in df.columns if "incidence" in c.lower() or "e_inc" in c.lower()]

    if year_cols and inc_cols:
        df = df[[year_cols[0], inc_cols[0]]].copy()
        df.columns = ["year", "tb_incidence_per_100k"]
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df = df.dropna()
        return df
    else:
        print("  [INFO] Could not identify year/incidence columns in WHO file — skipping.")
        return None


# ── 4. Merge & normalise ─────────────────────────────────────────────────────

def merge_and_normalise(nasa: pd.DataFrame, aqi: pd.DataFrame,
                        who: pd.DataFrame | None) -> pd.DataFrame:
    # Join on city + year (inner join to keep only overlapping city-years)
    merged = pd.merge(nasa, aqi, on=["city", "year"], how="inner")
    print(f"  After NASA × AQI merge: {merged.shape}")

    if who is not None:
        merged = pd.merge(merged, who, on="year", how="left")
        print(f"  After WHO merge: {merged.shape}")

    # Identify numeric feature columns (everything except city, year)
    id_cols  = ["city", "year"]
    feat_cols = [c for c in merged.columns if c not in id_cols]

    # MinMax scale
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(merged[feat_cols].fillna(merged[feat_cols].mean()))
    scaled_df = pd.DataFrame(scaled, columns=[f"{c}_scaled" for c in feat_cols])

    result = pd.concat([merged[id_cols].reset_index(drop=True),
                        merged[feat_cols].reset_index(drop=True),
                        scaled_df], axis=1)
    return result


# ── 5. Main ──────────────────────────────────────────────────────────────────

def main():
    print("=== Environmental Preprocessing ===\n")

    print("[1] Loading NASA POWER city CSVs …")
    nasa = load_nasa_all()
    print(f"    NASA data shape: {nasa.shape}")
    print(f"    Cities: {sorted(nasa['city'].unique())}")
    print(f"    Years : {sorted(nasa['year'].unique())}\n")

    print("[2] Loading India AQI data …")
    aqi = load_aqi()
    print(f"    AQI data shape: {aqi.shape}")
    print(f"    Cities: {sorted(aqi['city'].unique())}")
    print(f"    Years : {sorted(aqi['year'].unique())}\n")

    print("[3] Loading WHO TB incidence data (optional) …")
    who = load_who()
    print()

    print("[4] Merging and normalising …")
    env = merge_and_normalise(nasa, aqi, who)
    print(f"    Final env_features shape: {env.shape}\n")

    out_path = OUT_DIR / "env_features.csv"
    env.to_csv(out_path, index=False)
    print(f"[5] Saved → {out_path}")

    print("\n=== Summary ===")
    print(env[["city", "year"] + [c for c in env.columns
               if c not in ("city", "year") and "_scaled" not in c]].describe())


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).resolve().parent.parent)   # project root
    main()
