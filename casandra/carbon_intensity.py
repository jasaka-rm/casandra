"""
Reads your curated CSV (ticker, Scope 1+2 tonnes CO₂e, GLA sqm), computes kgCO₂e/sqm, and maps to a carbon score (0–100).

Goal: kgCO2e / sqm for the REIT.
Sources (in order): 
1) XBRL companyfacts for emissions & floor area (rarely complete)
2) Sustainability PDFs (manual extract -> CSV)
3) Fallback heuristic by property type

MVP: read a CSV you curate with columns:
    ticker, scope12_tonnes_co2e, gross_leasable_area_sqm
"""

import math, pandas as pd
from typing import Optional, Union

def carbon_intensity_from_csv(csv_path: str, ticker: str) -> Optional[float]:
    df = pd.read_csv(csv_path)
    row = df[df["ticker"].str.upper() == ticker.upper()].head(1)
    if row.empty:
        return None
    t = float(row.iloc[0]["scope12_tonnes_co2e"])
    a = float(row.iloc[0]["gross_leasable_area_sqm"])
    if a <= 0:
        return None
    kg_per_sqm = (t * 1000) / a
    return kg_per_sqm

def _load_carbon_df(carbon: Union[str, "pd.DataFrame"]) -> pd.DataFrame:
    if isinstance(carbon, pd.DataFrame):
        df = carbon.copy()
    else:
        df = pd.read_csv(carbon)
    # normalize column names
    df.columns = [c.strip().lower() for c in df.columns]
    required = {"ticker", "scope12_tonnes_co2e", "gross_leasable_area_sqm"}
    missing = required.difference(set(df.columns))
    if missing:
        raise ValueError(f"carbon_inputs is missing columns: {sorted(missing)}")
    return df

def carbon_intensity_kg_per_sqm(carbon: Union[str, "pd.DataFrame"], ticker: str) -> Optional[float]:
    df = _load_carbon_df(carbon)
    # robust ticker match
    row = df[df["ticker"].astype(str).str.upper() == ticker.upper()].head(1)
    if row.empty:
        return None
    t = row["scope12_tonnes_co2e"].iloc[0]
    gla = row["gross_leasable_area_sqm"].iloc[0]
    if pd.isna(t) or pd.isna(gla) or gla == 0:
        return None
    kg = float(t) * 1000.0
    return kg / float(gla)

def carbon_score_0_100(kg_per_sqm: Optional[float]) -> float:
    """
    Map intensity to 0–100 (higher = worse).
    Simple breakpoints; tune later by sector.
    """
    if kg_per_sqm is None:
        return 50.0  # unknown -> neutral
    if kg_per_sqm < 3:   return 10.0
    if kg_per_sqm < 8:   return 35.0
    if kg_per_sqm < 15:  return 60.0
    if kg_per_sqm < 25:  return 80.0
    return 95.0
