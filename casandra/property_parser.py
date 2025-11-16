'''
Pulls the “Item 2. Properties” section from the 10-K and extracts location lines (tables/bullets). 
Output: a deduplicated list like [{ "address": "City, ST | …" }, …].
'''

# casandra/property_parser.py

import re
from bs4 import BeautifulSoup

# --- dynamic parser ---
def _make_soup(html: str) -> BeautifulSoup:
    s = html.lstrip().lower()
    # Inline XBRL often starts with <?xml ...> but still has <html ...>
    if s.startswith("<?xml") and "<html" not in s[:2000]:
        return BeautifulSoup(html, features="xml")   # true XML without <html>
    return BeautifulSoup(html, "lxml")               # default & XHTML case

# --- robust section matchers (text only) ---
SECTION_RE = re.compile(r'\bITEM[\s\u00A0]*2\b.*\bPROPERTIES\b', re.I)
NEXT_RE    = re.compile(r'\bITEM[\s\u00A0]*3\b|\bPART[\s\u00A0]*II\b|\bSIGNATURES\b', re.I)

def extract_item2_tables_html(html: str) -> str | None:
    """
    Returns a concatenated HTML string of all <table> elements that appear
    after the 'Item 2 ... Properties' heading and before the next major section.
    Falls back to None if nothing is found.
    """
    soup = _make_soup(html)

    # 1) find the heading text node (string) anywhere in the doc
    heading_str = soup.find(string=lambda t: isinstance(t, str) and SECTION_RE.search(t))
    if not heading_str:
        return None

    # 2) find the next section boundary (text) after heading
    end_str = None
    try:
        end_str = heading_str.find_next(string=lambda t: isinstance(t, str) and NEXT_RE.search(t))
    except Exception:
        end_str = None

    # 3) walk forward from the heading, collecting tables until we hit the end_str
    tables = []
    cur = heading_str.parent  # start from the element containing the heading
    seen_heading = False
    while cur is not None:
        # Mark that we've moved past the heading node
        if cur is heading_str or getattr(cur, "string", None) is heading_str:
            seen_heading = True

        if seen_heading:
            # stop at next section
            if end_str is not None and (cur is end_str or getattr(cur, "string", None) is end_str):
                break
            if getattr(cur, "name", None) == "table":
                tables.append(cur)

        cur = cur.next_element

    if tables:
        return "".join(str(t) for t in tables)

    # 4) Fallback: some filings don't put tables immediately after the heading.
    #    As a fallback, return None here and let the caller scan the whole doc.
    return None



def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\u00A0", " ")).strip()

def parse_property_addresses(item2_or_full_html: str, full_html_if_needed: str | None = None) -> list[dict]:
    """
    Try to parse addresses from the Item 2 tables. If no tables are found,
    fall back to scanning the entire document for tables that look like the
    properties listing.
    """
    out = []

    def parse_tables_from_html(html_fragment: str) -> list[dict]:
        local = []
        soup = _make_soup(html_fragment)
        tables = soup.find_all("table")
        if not tables:
            return local

        current_region = None

        for table in tables:
            rows = table.find_all("tr")
            if not rows:
                continue

            # Detect a properties table (header contains "Property" and either "% Ownership" or "Type")
            header_cells = [_norm(x.get_text()) for x in rows[0].find_all(["th", "td"])]
            header_text = " ".join(h.lower() for h in header_cells)
            looks_like_props = ("property" in header_text) and (("% ownership" in header_text) or ("type" in header_text))
            if not looks_like_props:
                continue

            for tr in rows[1:]:
                cells = [_norm(td.get_text()) for td in tr.find_all(["td", "th"])]
                if not cells:
                    continue
                # Region header like "NEW YORK:"
                if len(cells) == 1 and cells[0].endswith(":") and cells[0].upper() == cells[0]:
                    current_region = cells[0].rstrip(":").title()
                    continue
                # Skip empty/header rows
                if not cells[0] or "property" in cells[0].lower():
                    continue

                prop_name = cells[0]
                addr = f"{prop_name}, {current_region}" if current_region else prop_name
                local.append({"address": addr})
        return local

    # First: attempt parsing only the Item 2 tables we extracted
    if item2_or_full_html:
        out = parse_tables_from_html(item2_or_full_html)

    # Fallback: if nothing parsed and we were given full HTML, scan *all* tables
    if not out and full_html_if_needed:
        out = parse_tables_from_html(full_html_if_needed)

    return out

