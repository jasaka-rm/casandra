'''
Pulls the “Item 2. Properties” section from the 10-K and heuristically extracts location lines (tables/bullets). 
Output: a deduplicated list like [{ "address": "City, ST | …" }, …].
'''


import re
from bs4 import BeautifulSoup
from typing import List, Dict

ITEM2_PATTERN = re.compile(r"(Item\s+2\.\s*Properties)(.*?)(Item\s+3\.)", re.IGNORECASE | re.DOTALL)

def extract_item2_block(filing_text: str) -> str:
    m = ITEM2_PATTERN.search(filing_text)
    if not m:
        # fallback: try "Properties" section alone
        alt = re.search(r"Properties(.*?)(Legal Proceedings|Item\s+3\.)", filing_text, re.I | re.S)
        if alt:
            return alt.group(1)
        raise RuntimeError("Could not locate Item 2. Properties section.")
    return m.group(2)

def parse_property_addresses(item2_html: str) -> List[Dict]:
    """
    Heuristic parser: look for HTML tables & lists with location-like cells.
    Returns [{address: str}] — keep it simple for MVP.
    """
    soup = BeautifulSoup(item2_html, "lxml")
    props = []

    # 1) Parse tables
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
            # crude heuristics: look for city/state or country strings
            cell_line = " | ".join(cells)
            if re.search(r"\b[A-Z][a-z]+,\s*[A-Z]{2}\b", cell_line) or re.search(r"\b(UK|United Kingdom|Germany|France|Japan|USA|United States)\b", cell_line, re.I):
                props.append({"address": cell_line})

    # 2) Parse bullet lists mentioning "Property", "Location"
    for li in soup.find_all("li"):
        txt = li.get_text(" ", strip=True)
        if "Location" in txt or re.search(r"\b[A-Z][a-z]+,\s*[A-Z]{2}\b", txt):
            props.append({"address": txt})

    # De-duplicate
    seen = set()
    uniq = []
    for p in props:
        a = p["address"]
        if a not in seen:
            uniq.append(p)
            seen.add(a)
    return uniq
