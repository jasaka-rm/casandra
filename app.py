# app.py — Streamlit dashboard for CASANDRA

import io
import json
from pathlib import Path

import streamlit as st
import pandas as pd

# Try to import your package. Your folder has been called "casandra" in your paths.
# If you renamed it to "reitvision_esg", the fallback will work.
try:
    from casandra.demo_pipeline import score_reit
    from casandra.config import WEIGHTS as DEFAULT_WEIGHTS, SEC_USER_AGENT
except Exception:
    from reitvision_esg.demo_pipeline import score_reit
    from reitvision_esg.config import WEIGHTS as DEFAULT_WEIGHTS, SEC_USER_AGENT

st.set_page_config(page_title="CASANDRA", page_icon="🏙️", layout="wide")

st.title("🏙️ CASANDRA — Dashboard")
st.caption("MVP interface to score REITs using climate, carbon, and governance factors.")

with st.sidebar:
    st.header("Inputs")
    cik = st.text_input("CIK (no leading zeros required)", value="0000790703")
    name = st.text_input("REIT Name", value="Simon Property Group")
    ticker = st.text_input("Ticker", value="SPG")
    max_props = st.slider("Max properties to parse", 3, 40, 10, 1)

    st.markdown("---")
    st.subheader("Weights (sum to 100%)")
    w_climate = st.slider("Climate weight (%)", 0, 100, int(DEFAULT_WEIGHTS.get("climate", 1/3)*100))
    w_carbon  = st.slider("Carbon weight (%)", 0, 100, int(DEFAULT_WEIGHTS.get("carbon", 1/3)*100))
    w_gov     = st.slider("Governance weight (%)", 0, 100, int(DEFAULT_WEIGHTS.get("gov", 1/3)*100))
    total_w = w_climate + w_carbon + w_gov
    if total_w == 0:
        st.warning("Weights must sum to > 0. Adjust the sliders.")
    else:
        st.caption(f"Current total: **{total_w}%**")

    st.markdown("---")
    st.subheader("Carbon CSV upload")
    st.caption("CSV with columns: `ticker, scope12_tonnes_co2e, gross_leasable_area_sqm`")
    carbon_file = st.file_uploader("Upload carbon_inputs.csv", type=["csv"])

    st.markdown("---")
    st.subheader("SEC User-Agent")
    st.write(f"Using: `{SEC_USER_AGENT}`")
    st.caption("Edit in config.py if needed.")

    run_btn = st.button("▶️ Run scoring")

# Save uploaded CSV to a temp file if provided
temp_csv_path = None
if carbon_file is not None:
    temp_csv_path = Path(st.experimental_user_input_stream() if hasattr(st, "experimental_user_input_stream") else ".") / "uploaded_carbon_inputs.csv"
    # Write to disk
    data = carbon_file.read()
    with open(temp_csv_path, "wb") as f:
        f.write(data)

# Normalize weights to 0..1
def normalize_weights(a, b, c):
    s = a + b + c
    if s == 0:
        return {"climate": 1/3, "carbon": 1/3, "gov": 1/3}
    return {"climate": a/s, "carbon": b/s, "gov": c/s}

user_weights = normalize_weights(w_climate, w_carbon, w_gov)

col_left, col_right = st.columns([1.1, 1])

if run_btn:
    with st.spinner("Scoring REIT… (fetching SEC filing, geocoding, climate, news)"):
        try:
            # Call pipeline
            res = score_reit(
                cik=cik,
                name=name,
                ticker=ticker,
                carbon_csv=str(temp_csv_path) if temp_csv_path else "carbon_inputs.csv",
                max_props=max_props
            )

            # Recombine with custom weights (if your pipeline always uses config weights,
            # you can optionally recompute final scores here from sub-scores)
            climate_score = res["climate_score"]
            carbon_score  = res["carbon_score"]
            gov_1y = res["gov_score_1y"]
            gov_5y = res["gov_score_5y"]
            gov_10y = res["gov_score_10y"]

            # Combine with user weights
            def combine(c, ca, g, w):
                return round(w["climate"]*c + w["carbon"]*ca + w["gov"]*g, 2)

            final_1y  = combine(climate_score, carbon_score, gov_1y,  user_weights)
            final_5y  = combine(climate_score, carbon_score, gov_5y,  user_weights)
            final_10y = combine(climate_score, carbon_score, gov_10y, user_weights)

            # Left: numbers + chart
            with col_left:
                st.success("Done!")
                st.subheader("Scores")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Climate (0–100)", f"{climate_score}")
                m2.metric("Carbon (0–100)",  f"{carbon_score}")
                m3.metric("Gov 1y (0–100)",  f"{gov_1y}")
                m4.metric("#Props used",     f"{res['n_properties_used']}")

                st.subheader("ESG-Adjusted Distress (0–100, higher=worse)")
                df_chart = pd.DataFrame({
                    "Horizon": ["1y", "5y", "10y"],
                    "Score": [final_1y, final_5y, final_10y]
                }).set_index("Horizon")
                st.bar_chart(df_chart)

            # Right: JSON + download
            with col_right:
                st.subheader("Result JSON")
                out = {
                    "inputs": {"cik": cik, "name": name, "ticker": ticker, "weights": user_weights},
                    "scores": {
                        "climate": climate_score,
                        "carbon": carbon_score,
                        "governance": {"1y": gov_1y, "5y": gov_5y, "10y": gov_10y},
                        "final": {"1y": final_1y, "5y": final_5y, "10y": final_10y}
                    },
                    "n_properties_used": res["n_properties_used"]
                }
                st.code(json.dumps(out, indent=2), language="json")

                buf = io.BytesIO(json.dumps(out, indent=2).encode("utf-8"))
                st.download_button("Download results (JSON)", data=buf, file_name=f"{ticker}_reitvision_esg.json", mime="application/json")

        except Exception as e:
            st.error(f"Error while scoring: {e}")
            st.stop()

st.markdown("---")
st.caption("Tip: if carbon data is missing for a ticker, the app uses a neutral carbon score (50) in the MVP.")
