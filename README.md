# 🏙️ REITVision ESG — Real Estate ESG Risk Intelligence

**REITVision ESG** is a Python-based analytics tool that combines financial, climate, and governance data to evaluate the **ESG-adjusted risk** of Real Estate Investment Trusts (REITs).  
It scrapes public filings, estimates climate and carbon exposure, analyzes governance sentiment, and generates predictive ESG distress scores across **1-, 5-, and 10-year** horizons.
It includes both a data pipeline and a Streamlit web app (app.py) for visualizing results and running analyses through an intuitive interface.

---

## 🚀 Overview

### Why
Traditional REIT analysis misses emerging ESG risks — such as carbon penalties, flood exposure, or governance controversies — that can destroy portfolio value.  
**REITVision ESG** integrates these signals into one unified score to help investors:
- Detect early sustainability and financial risks  
- Avoid stranded or “brown” assets  
- Identify climate-resilient, well-governed REITs

### What It Does
1. **Scrapes REIT data** from SEC/EDGAR filings (Item 2 – Properties)  
2. **Geocodes property locations** and assesses **physical climate risk** (heat & flood exposure)  
3. **Estimates carbon intensity** (kg CO₂e / sqm) from sustainability disclosures  
4. **Analyzes governance sentiment** using NLP (VADER on Google News)  
5. Combines all three into an **ESG-Adjusted Distress Score (0-100)**  
6. Calculates predictive metrics for **1-, 5-, and 10-year** horizons  
7. (Optional) Links ESG metrics to future **price-drop probability** (>20 % in 12 months)

---

## ⚙️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/jasaka-rm/casandra.git
cd casandra

# 2. Create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---


## 🧩 Usage Example
```bash
from reitvision_esg.demo_pipeline import score_reit

result = score_reit(
    cik="0000790703",           # Example: Simon Property Group
    name="Simon Property Group",
    ticker="SPG",
    carbon_csv="reitvision_esg/carbon_inputs.csv",
    max_props=10
)

print(result)
```

```bash
Example output

{
  'climate_score': 58.4,
  'carbon_score': 35.0,
  'gov_score_1y': 52.3,
  'final_esg_1y': 48.9,
  'final_esg_5y': 47.4,
  'final_esg_10y': 46.7,
  'n_properties_used': 8
}
```

## 🎛️ Interactive Dashboard (Streamlit)
We’ve built a simple Streamlit app (app.py) to visualize and interact with the REITVision ESG model.
It lets you enter a REIT name, ticker, and CIK number, then runs the full ESG-scoring pipeline and displays results instantly in a web dashboard.

🧭 How to launch it
Make sure your virtual environment is activated and dependencies are installed:
```bash
pip install -r requirements.txt
```

Run the app:
```bash
streamlit run app.py
```

Open your browser at: 
http://localhost:8501

🧩 Features
Input REIT CIK, name, ticker, and optional CSV path
See ESG metrics for 1-, 5-, and 10-year horizons
JSON summary + individual metrics displayed in real time
Works entirely with Python — no extra setup needed



## 🧮 Project Structure
reitvision_esg/
│
├── config.py                # Settings (weights, timeouts, user-agent)
├── edgar_scraper.py         # Scrape SEC filings
├── property_parser.py       # Extract property addresses from 10-K
├── geocode.py               # Geocode addresses via OpenStreetMap
├── climate_risk.py          # Compute flood/heat risk (0–100)
├── carbon_intensity.py      # Compute carbon intensity score
├── governance_sentiment.py  # NLP sentiment for governance risk
├── scoring.py               # Combine 3 metrics into ESG score
└── demo_pipeline.py         # Orchestration pipeline


## Future Work