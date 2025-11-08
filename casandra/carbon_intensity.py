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
from typing import Optional

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
