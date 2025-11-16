"""
Orchestrates the whole flow for a single REIT:
EDGAR → properties → geocode → climate → carbon → governance (1y/5y/10y) → final scores. 
Returns a dict with all component and final scores.

End-to-end demo for a single REIT:
- Pull 10-K
- Extract Item 2 properties
- Geocode first N addresses
- Compute climate risk per property; average to REIT climate score
- Get carbon intensity (CSV)
- Compute governance risk (1y window by default)
- Combine into final score; repeat for 1y/5y/10y if desired by changing lookback and climate horizon
"""

# casandra/demo_pipeline.py

from __future__ import annotations
from statistics import mean
import pandas as pd

from .config import SEC_USER_AGENT
from .edgar_scraper import download_10k_text
from .property_parser import extract_item2_tables_html, parse_property_addresses
from .geocode import geocode_address
from .climate_risk import climate_risk_0_100
from .carbon_inputs_dynamic import get_carbon_row
from .carbon_intensity import carbon_intensity_kg_per_sqm, carbon_score_0_100
from .governance_sentiment import governance_risk_score_0_100
from .scoring import combine_scores

WINDOWS = {"1y": 365, "5y": 365*5, "10y": 365*10}


def score_reit(
    *,
    cik: str,
    name: str,
    ticker: str
) -> dict:
    # 1) filings -> addresses
    filing_text = download_10k_text(cik)
    print("Downloaded 10-K length:", len(filing_text or ""))
    print("First 300 chars:", (filing_text or "")[:300])
    item2_text = extract_item2_tables_html(filing_text)
    props = parse_property_addresses(item2_text)

    # 2) geocode & climate scores
    c_scores = []
    for p in props:
        addr = p.get("address") or p.get("full_address") or ""
        if not addr:
            continue
        g = geocode_address(addr, user_agent=SEC_USER_AGENT)
        if not g or "lat" not in g or "lon" not in g:
            continue
        c_scores.append(climate_risk_0_100(float(g["lat"]), float(g["lon"])))

    climate = mean(c_scores) if c_scores else 50.0  # neutral if nothing parsed

    # 3) carbon intensity — always dynamic
    row = get_carbon_row(ticker=ticker, cik=cik, company_name=name)
    carbon_df = pd.DataFrame([row])  # dynamic DataFrame only
    ci_kg_per_sqm = carbon_intensity_kg_per_sqm(carbon_df, ticker)
    carbon = carbon_score_0_100(ci_kg_per_sqm)

    # 4) governance
    gov_1y = governance_risk_score_0_100(name, WINDOWS["1y"])
    gov_5y = governance_risk_score_0_100(name, WINDOWS["5y"])
    gov_10y = governance_risk_score_0_100(name, WINDOWS["10y"])

    # Combine
    esg_1y = combine_scores(climate, carbon, gov_1y)
    esg_5y = combine_scores(climate, carbon, gov_5y)
    esg_10y = combine_scores(climate, carbon, gov_10y)

    return {
        "climate_score": round(float(climate), 2),
        "carbon_score": round(float(carbon), 2),
        "gov_score_1y": round(float(gov_1y), 2),
        "gov_score_5y": round(float(gov_5y), 2),
        "gov_score_10y": round(float(gov_10y), 2),
        "final_esg_1y": round(float(esg_1y), 2),
        "final_esg_5y": round(float(esg_5y), 2),
        "final_esg_10y": round(float(esg_10y), 2),
        "n_properties_used": len(c_scores),
    }
