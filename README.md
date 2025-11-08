# 🏙️ REITVision ESG — Real Estate ESG Risk Intelligence

**REITVision ESG** is a Python-based analytics tool that combines financial, climate, and governance data to evaluate the **ESG-adjusted risk** of Real Estate Investment Trusts (REITs).  
It scrapes public filings, estimates climate and carbon exposure, analyzes governance sentiment, and generates predictive ESG distress scores across **1-, 5-, and 10-year** horizons.

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
