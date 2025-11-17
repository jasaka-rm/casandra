'''
Pulls the “Item 2. Properties” section from the 10-K and extracts location lines (tables/bullets). 
Output: a deduplicated list like [{ "address": "City, ST | …" }, …].
'''



import re
from bs4 import BeautifulSoup
import pandas as pd
from casandra.edgar_scraper import download_10k_text
# from casandra.property_parser import extract_item2_tables_html


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

def _find_col(colnames, *candidates):
    """Return the first column name that fuzzy-matches any candidate."""
    low = {str(c).strip().lower(): c for c in colnames}
    for c in colnames:
        lc = str(c).strip().lower()
        for cand in candidates:
            if cand in lc:
                return low[lc]
    return None

def parse_property_addresses(item2_html: str, full_html_if_needed: str | None = None) -> list[dict]:
    """
    Parse addresses from Item 2 tables using pandas.read_html, which handles
    colspans/rowspans/spacer cells better than manual HTML walking.
    We look for a table containing both a 'Property'/'Properties' column and a 'Location' column.
    Returns [{'address': 'Property Name, Location'}, ...]
    """
    def parse_html_with_pandas(html_fragment: str) -> list[dict]:
        out = []
        try:
            dfs = pd.read_html(html_fragment, flavor="lxml")
        except ValueError:
            return out  # no tables
        for df in dfs:
            # flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [" ".join([_norm(str(x)) for x in tup if x is not None]).strip() for tup in df.columns.values]
            else:
                df.columns = [_norm(str(c)) for c in df.columns]

            # find key columns (case-insensitive, fuzzy)
            prop_col = _find_col(df.columns, "property", "properties")
            loc_col  = _find_col(df.columns, "location")

            if not prop_col or not loc_col:
                continue

            # clean rows (drop all-empty)
            df = df[[prop_col, loc_col]].copy()
            df[prop_col] = df[prop_col].astype(str).map(_norm)
            df[loc_col]  = df[loc_col].astype(str).map(_norm)

            # drop banner/section rows (e.g., 'Residential Communities', 'Office Building')
            banners = set(["residential communities", "office building", "office buildings", "retail", "industrial"])
            mask_banner = df[loc_col].str.len().eq(0) & df[prop_col].str.lower().isin(banners)

            # keep rows with both fields non-empty
            mask_valid = df[prop_col].ne("").astype(bool) & df[loc_col].ne("").astype(bool) & (~mask_banner)
            for _, row in df[mask_valid].iterrows():
                out.append({"address": f"{row[prop_col]}, {row[loc_col]}"})
        return out

    props = parse_html_with_pandas(item2_html or "")
    if not props and full_html_if_needed:
        props = parse_html_with_pandas(full_html_if_needed)
    return props


def extract_addresses_from_table0_col0(cik: str) -> pd.DataFrame:
    """
    Download the latest 10-K for a CIK, parse Item 2 tables,
    and extract property addresses from Table 0, column 0.
    Returns a DataFrame with a single 'address' column.
    """
    html = download_10k_text(cik)
    blk  = extract_item2_tables_html(html)
    dfs  = pd.read_html(blk, flavor="lxml")
    df0  = dfs[0]  # Table 0 is the properties table

    s = df0.iloc[:, 0].astype(str).str.strip()
    s = s[s.ne("")]
    s = s[~s.str.fullmatch(r"(?i)property|properties")]
    s = s[~s.str.contains(r"(?i)\bSEGMENT\b")]
    s = s.str.replace(r"\(\d+\)", "", regex=True).str.replace(r"\s{2,}", " ", regex=True).str.strip()

    addresses = list(dict.fromkeys(s.tolist()))
    return pd.DataFrame({"address": addresses})