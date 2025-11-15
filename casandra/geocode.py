'''
Turns each address into lat/lon using OpenStreetMap Nominatim (polite rate limiting). 
Output: {"lat": …, "lon": …, "display_name": …} for each address.
'''

import time, requests
from typing import Dict, Optional
from .config import REQUEST_TIMEOUT

NOMINATIM = "https://nominatim.openstreetmap.org/search"

def geocode_address(addr: str, user_agent: str) -> Optional[Dict]:
    params = {"q": addr, "format": "json", "limit": 1}
    r = requests.get(NOMINATIM, params=params, headers={"User-Agent": user_agent}, timeout=REQUEST_TIMEOUT)
    if r.status_code != 200:
        return None
    js = r.json()
    if not js:
        return None
    # be polite
    time.sleep(1)
    return {"lat": float(js[0]["lat"]), "lon": float(js[0]["lon"]), "display_name": js[0]["display_name"]}
