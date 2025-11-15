"""
MVP climate proxies (0–100, higher = worse):
- Heat risk via Open-Meteo climate API (projected July max temp mid-century).
- Flood risk via Open-Elevation (low elevation ⇒ higher risk).
Combines sub-risks into a single climate risk score.

Proxies:
- Heat risk proxy: projected change in hottest-day temperature via Open-Meteo CMIP6 API
- Flood proxy: low elevation heuristic using Open-Elevation; coastal proximity via reverse geocoding country + known coastline flag (very rough)
- Wildfire proxy: use recent burned area climatology proxy (skip for MVP or set neutral)

All scores are mapped to 0–100 (higher = WORSE risk).
"""

import math, requests
from typing import Dict
from .config import REQUEST_TIMEOUT

OPEN_METEO = "https://climate-api.open-meteo.com/v1/climate"
OPEN_ELEV = "https://api.open-elevation.com/api/v1/lookup"

def heat_risk_score(lat: float, lon: float) -> float:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_year": 2031, "end_year": 2060,  # mid-term window
        "month": 7,  # hottest month in many N. Hemisphere locations;
        "models": "MPI-ESM1-2-LR",
        "daily": "temperature_2m_max",
    }
    r = requests.get(OPEN_METEO, params=params, timeout=REQUEST_TIMEOUT)
    if r.status_code != 200:
        return 50.0
    js = r.json()
    # crude delta vs. 1991-2020 baseline if available; else map absolute max to risk
    mx = max(js.get("daily", {}).get("temperature_2m_max", [30]))
    # map 30–50°C -> 20–100 risk
    return max(0, min(100, (mx - 30) * 4 + 20))

def elevation_meters(lat: float, lon: float) -> float:
    r = requests.get(OPEN_ELEV, params={"locations": f"{lat},{lon}"}, timeout=REQUEST_TIMEOUT)
    if r.status_code != 200:
        return 50.0
    js = r.json()
    if "results" in js and js["results"]:
        return float(js["results"][0]["elevation"])
    return 50.0

def flood_risk_score(lat: float, lon: float) -> float:
    elev = elevation_meters(lat, lon)
    # naive mapping: <3m extremely high, 3–10m high, 10–50m moderate, >50m low
    if elev < 3:   return 95.0
    if elev < 10:  return 80.0
    if elev < 50:  return 55.0
    if elev < 200: return 30.0
    return 15.0

def climate_risk_0_100(lat: float, lon: float) -> float:
    heat = heat_risk_score(lat, lon)
    flood = flood_risk_score(lat, lon)
    # MVP: equal average of two sub-risks (0-100 higher = worse)
    return (heat + flood) / 2.0
