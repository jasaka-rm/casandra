'''
Talks to SEC EDGAR. Finds the latest 10-K for a CIK (Central Index Key, every company has onoe) and downloads the primary document (often HTML). 
Returns raw text for parsing.
'''

import time, requests
from typing import Dict, Any
from .config import SEC_USER_AGENT, REQUEST_TIMEOUT, REQUEST_SLEEP

BASE = "https://data.sec.gov"

HEADERS = {"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "gzip, deflate"}

def get_submissions(cik_nozeros: str) -> Dict[str, Any]:
    url = f"{BASE}/submissions/CIK{cik_nozeros.zfill(10)}.json"
    r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()

def latest_10k_primary_doc_url(cik_nozeros: str) -> str:
    data = get_submissions(cik_nozeros)
    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    acc = filings.get("accessionNumber", [])
    prim = filings.get("primaryDocument", [])
    for f, a, p in zip(forms, acc, prim):
        if f == "10-K":
            # Convert CIK + accession to archive URL
            acc_nodash = a.replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{int(cik_nozeros)}/{acc_nodash}/{p}"
            time.sleep(REQUEST_SLEEP)
            return url
    raise RuntimeError("No 10-K found in recent filings.")

def download_10k_text(cik_nozeros: str) -> str:
    url = latest_10k_primary_doc_url(cik_nozeros)
    r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    # Some filings are HTML; return raw text for downstream parsing
    return r.text


if __name__ == "__main__":
    # Example: test a few public companies
    test_ciks = {
        "VRT": "0000899689",     
        "SPG": "0000790703",     
    }

    for name, cik in test_ciks.items():
        print(f"\n=== {name} ({cik}) ===")
        try:
            url = latest_10k_primary_doc_url(cik)
            print(f"10-K URL: {url}")

            text = download_10k_text(cik)
            print(f"Retrieved {len(text):,} characters of text.")

            # Optional: preview a few lines
            # print(text[:500])
        except Exception as e:
            print(f"Error for {name}: {e}")
