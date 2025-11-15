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

from statistics import mean
from .edgar_scraper import download_10k_text
from .property_parser import extract_item2_block, parse_property_addresses
from .geocode import geocode_address
from .climate_risk import climate_risk_0_100
from .carbon_intensity import carbon_intensity_from_csv, carbon_score_0_100
from .governance_sentiment import governance_risk_score_0_100
from .config import SEC_USER_AGENT, WINDOWS
from .scoring import combine_scores

def score_reit(cik: str, name: str, ticker: str, carbon_csv: str, max_props: int = 10):
    # 1) filings -> addresses
    filing = download_10k_text(cik)
    item2 = extract_item2_block(filing)
    props = parse_property_addresses(item2)
    props = props[:max_props]

    # 2) geocode & climate scores
    c_scores = []
    for p in props:
        g = geocode_address(p["address"], user_agent=SEC_USER_AGENT)
        if not g: 
            continue
        c_scores.append(climate_risk_0_100(g["lat"], g["lon"]))
    climate = mean(c_scores) if c_scores else 50.0

    # 3) carbon intensity
    ci = carbon_intensity_from_csv(carbon_csv, ticker)
    carbon = carbon_score_0_100(ci)

    # 4) governance (1y as default window)
    gov_1y = governance_risk_score_0_100(name, WINDOWS["1y"])

    # Combine
    esg_1y = combine_scores(climate, carbon, gov_1y)

    # Optionally compute 5y/10y variants (news lookback alters governance; climate can use different horizons if you change API params)
    gov_5y = governance_risk_score_0_100(name, WINDOWS["5y"])
    gov_10y = governance_risk_score_0_100(name, WINDOWS["10y"])
    esg_5y = combine_scores(climate, carbon, gov_5y)
    esg_10y = combine_scores(climate, carbon, gov_10y)

    return {
        "climate_score": round(climate,2),
        "carbon_score": round(carbon,2),
        "gov_score_1y": round(gov_1y,2),
        "gov_score_5y": round(gov_5y,2),
        "gov_score_10y": round(gov_10y,2),
        "final_esg_1y": esg_1y,
        "final_esg_5y": esg_5y,
        "final_esg_10y": esg_10y,
        "n_properties_used": len(c_scores),
    }
