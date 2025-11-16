import streamlit as st
import pandas as pd
import altair as alt

from casandra.demo_pipeline import score_reit
from casandra.config import WEIGHTS as DEFAULT_WEIGHTS, SEC_USER_AGENT
from casandra.price_projection import get_current_price_yf, project_prices_from_scores

st.set_page_config(page_title="CASANDRA", page_icon="🏙️", layout="wide")

st.title("🏙️ CASANDRA — Dashboard")
st.caption("MVP interface to score REITs using climate, carbon, and governance factors.")

# Show instructions only if the scoring button hasn't been pressed yet
if "scoring_done" not in st.session_state or not st.session_state.scoring_done:
    st.badge(
        "💡 **Enter a REIT ticker and click **Run Scoring** below to generate the ESG forecast**"
    )

with st.sidebar:
    st.header("Inputs")
    cik = st.text_input("CIK (no leading zeros required)", value="0000899689")
    name = st.text_input("REIT Name", value="Vornado Realty Trust")
    ticker = st.text_input("Ticker", value="VRT")

    st.markdown("---")
    st.subheader("Weights (sum to 100%)")
    w_climate = st.slider("Climate weight (%)", 0, 100, int(DEFAULT_WEIGHTS.get("climate", 1/3)*100))
    w_carbon  = st.slider("Carbon weight (%)", 0, 100, int(DEFAULT_WEIGHTS.get("carbon", 1/3)*100))
    w_gov     = st.slider("Governance weight (%)", 0, 100, int(DEFAULT_WEIGHTS.get("gov", 1/3)*100))
    total_w = w_climate + w_carbon + w_gov
    if total_w == 0:
        st.warning("Weights must sum to > 0. Adjust the sliders.")
    elif total_w == 99:
        st.caption(f"Current total: **{total_w+1}%**")
    elif total_w == 100:
        st.caption(f"Current total: **{total_w}%**")
    else:
        st.warning("Weights must sum to > 0. Adjust the sliders.")

    st.markdown("---")

    run_btn = st.button("▶️ Run scoring")

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
                cik=cik.strip(),
                name=name.strip(),
                ticker=ticker.strip()
            )

            # Mark scoring as done (hides sidebar message)
            st.session_state.scoring_done = True

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

            # Left: numbers
            with col_left:
                st.subheader("Scores")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Climate (0–100)", f"{climate_score}")
                m2.metric("Carbon (0–100)",  f"{carbon_score}")
                m3.metric("Gov 1y (0–100)",  f"{gov_1y}")
                m4.metric("#Props used",     f"{res['n_properties_used']}")

                st.caption("Tip: if carbon data is missing for a ticker, the app uses a neutral carbon score (50) in the MVP.")
                st.success("Done!")

            # Right: graph
            with col_right:
                st.subheader("ESG-Adjusted Distress (0–100, higher=worse)")
                df_chart = pd.DataFrame({
                    "Horizon": pd.Categorical(["1y", "5y", "10y"], categories=["1y", "5y", "10y"], ordered=True),
                    "Score": [final_1y, final_5y, final_10y],
                })

                # --- Color mapping based on score ---
                def score_color(score):
                    if score <= 30:
                        return "#299530"   # dark green
                    elif score <= 60:
                        return "#008aed"   # grey-blue
                    elif score <= 80:
                        return "#e65100"   # orange
                    else:
                        return "#b71c1c"   # red

                df_chart["Color"] = df_chart["Score"].apply(score_color)

                # --- Altair chart ---
                chart = (
                    alt.Chart(df_chart)
                    .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                    .encode(
                        x=alt.X("Horizon", sort=["1y", "5y", "10y"], title="Horizon"),
                        y=alt.Y("Score", scale=alt.Scale(domain=[0, 100]), title="ESG Score"),
                        color=alt.Color("Color:N", scale=None, legend=None),
                        tooltip=["Horizon", "Score"]
                    )
                    .properties(width=400, height=300, title="ESG Score by Horizon")
                )

                st.altair_chart(chart, use_container_width=True)

        
            st.markdown("---")
            st.header("📈 Price Projections")

            if ticker and final_1y is not None and final_5y is not None and final_10y is not None:
                try:
                    current_price = get_current_price_yf(ticker)
                    proj = project_prices_from_scores(
                        current_price=current_price,
                        final_esg_1y=final_1y,
                        final_esg_5y=final_5y,
                        final_esg_10y=final_10y,
                    )

                    # Current price
                    st.subheader("Current")
                    st.metric("Current Price", f"${proj.current_price:,.2f}")

                    # Future horizons
                    from datetime import datetime
                    year_now = datetime.now().year
                    c1, c5, c10 = st.columns(3)

                    with c1:
                        st.subheader(f"In 1 Year ({year_now + 1})")
                        st.metric("Projected Price (1y)", f"${proj.price_1y:,.2f}", f"{proj.adj_pct_1y*100:+.2f}%")
                        st.caption(f"Final ESG 1y: {final_1y:.1f}")

                    with c5:
                        st.subheader(f"In 5 Years ({year_now + 5})")
                        st.metric("Projected Price (5y)", f"${proj.price_5y:,.2f}", f"{proj.adj_pct_5y*100:+.2f}%")
                        st.caption(f"Final ESG 5y: {final_5y:.1f}")

                    with c10:
                        st.subheader(f"In 10 Years ({year_now + 10})")
                        st.metric("Projected Price (10y)", f"${proj.price_10y:,.2f}", f"{proj.adj_pct_10y*100:+.2f}%")
                        st.caption(f"Final ESG 10y: {final_10y:.1f}")

                except Exception as pe:
                    st.info(f"Price projections unavailable: {pe}")
            else:
                st.info("Run a score first to enable price projections.")

        except Exception as e:
            st.error(f"Error while scoring: {e}")
            st.stop()

