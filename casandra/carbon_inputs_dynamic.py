# carbon_inputs_dynamic.py
from typing import Dict, Optional
from .edgar_scraper import download_10k_text 
from .property_parser import extract_item2_block  
from .config import SEC_USER_AGENT
import re, math, pandas as pd

def parse_gla_sqm_from_10k(html: str) -> Optional[float]:
    # 1) Try a direct “total gross leasable area” capture (feet or meters)
    text = re.sub(r'\s+', ' ', html, flags=re.I)
    m = re.search(r'(total\s+gross\s+leasable\s+area.*?)([\d,\.]+)\s*(square\s*feet|sq\.?\s*ft|sf|square\s*met(ers|res)|sqm)', text, re.I)
    if not m: 
        return None
    val = float(m.group(2).replace(',', ''))
    unit = m.group(3).lower()
    if 'feet' in unit or 'sq' in unit and 'm' not in unit:
        return val / 10.7639  # ft² → m²
    return val  # already m²

def fetch_scope12_tonnes_from_sustainability(ticker: str, company_name: str) -> Optional[float]:
    # Strategy: you already use NLP/news; here do a targeted fetch and parse
    #  - try latest PDF/HTML sustainability page
    #  - look for a table row containing “Scope 1” and “Scope 2”
    #  - extract numbers for the same fiscal year as the latest 10-K
    # Pseudocode placeholders below; implement with requests + pdfminer/camelot if PDF
    # return float(total_scope1 + total_scope2) or None
    return None  # implement

def get_carbon_row(ticker: str, cik: str, company_name: str) -> Dict[str, float]:
    html = download_10k_text(cik)
    gla_sqm = parse_gla_sqm_from_10k(html)
    scope12 = fetch_scope12_tonnes_from_sustainability(ticker, company_name)
    return {
        "ticker": ticker,
        "scope12_tonnes_co2e": scope12 if scope12 is not None else math.nan,
        "gross_leasable_area_sqm": gla_sqm if gla_sqm is not None else math.nan,
    }
