"""
Retrieve current stock price (Yahoo Finance) and project 1y/5y/10y prices
based on Casandra ESG scores using linear coefficients.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .demo_pipeline import score_reit

def get_current_price_yf(ticker: str) -> float:

    import yfinance as yf

    t = yf.Ticker(ticker)
    hist = t.history(period="1d")

    if hist.empty:
        raise ValueError(f"No price data returned for ticker {ticker!r}.")
    return float(hist["Close"].iloc[-1])


@dataclass
class Projections:
    current_price: float
    adj_pct_1y: float
    price_1y: float
    adj_pct_5y: float
    price_5y: float
    adj_pct_10y: float
    price_10y: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "current_price": self.current_price,
            "adj_pct_1y": self.adj_pct_1y,
            "price_1y": self.price_1y,
            "adj_pct_5y": self.adj_pct_5y,
            "price_5y": self.price_5y,
            "adj_pct_10y": self.adj_pct_10y,
            "price_10y": self.price_10y,
        }


def _linear_adjustment(score: float, beta: float) -> float:
    """Map a score (0-100) to a percentage adjustment using a simple linear rule.

    We center at 50 (neutral). Scores above 50 increase price; below decrease.
    adj_pct = beta * (score - 50) / 50

    Example (beta=0.10): score=60 -> +2.0%; score=40 -> -2.0%.
    """
    # Clamp score to [0,100] just in case
    s = max(0.0, min(100.0, float(score)))
    return beta * (s - 50.0) / 50.0 # Transform the score into a number bw -1 and 1 times the beta of each scenario

# Returns a class object with all the prices and adjustments
def project_prices_from_scores(
    current_price: float,
    final_esg_1y: float,
    final_esg_5y: float,
    final_esg_10y: float,
    beta_1y: float = 0.10,
    beta_5y: float = 0.20,
    beta_10y: float = 0.30,
) -> Projections:
    """Project prices using simple linear coefficients (betas).

    Betas are the *maximum* proportional move when score goes from 0 to 100.
    Defaults:
      1y:  ±10%   (beta_1y=0.10)
      5y:  ±20%   (beta_5y=0.20)
      10y: ±30%   (beta_10y=0.30)
    """
    adj1 = _linear_adjustment(final_esg_1y, beta_1y)
    adj5 = _linear_adjustment(final_esg_5y, beta_5y)
    adj10 = _linear_adjustment(final_esg_10y, beta_10y)

    p1 = current_price * (1.0 + adj1)
    p5 = current_price * (1.0 + adj5)
    p10 = current_price * (1.0 + adj10)

    return Projections(
        current_price=current_price,
        adj_pct_1y=adj1,
        price_1y=p1,
        adj_pct_5y=adj5,
        price_5y=p5,
        adj_pct_10y=adj10,
        price_10y=p10,
    )


def run_price_projection(
    ticker: str,
    cik: str,
    name: str,
    carbon_csv: Optional[str] = None,
    max_props: int = 10,
    beta_1y: float = 0.10,
    beta_5y: float = 0.20,
    beta_10y: float = 0.30,
) -> Dict[str, Any]:
    """End-to-end helper:
    1) fetch current price from Yahoo Finance
    2) run Casandra scoring pipeline
    3) project 1y/5y/10y prices using simple coefficients
    """
    # 1) current market price
    current = get_current_price_yf(ticker)

    # 2) ESG scores (uses the project's pipeline)
    scores = score_reit(
        cik=cik,
        name=name,
        ticker=ticker
    )

    # 3) price projections
    proj = project_prices_from_scores(
        current_price=current,
        final_esg_1y=float(scores.get("final_esg_1y")),
        final_esg_5y=float(scores.get("final_esg_5y")),
        final_esg_10y=float(scores.get("final_esg_10y")),
        beta_1y=beta_1y,
        beta_5y=beta_5y,
        beta_10y=beta_10y,
    )

    return {
        "ticker": ticker,
        "cik": cik,
        "name": name,
        "scores": scores,
        "current_price": proj.current_price,
        "adj_pct_1y": proj.adj_pct_1y,
        "price_1y": proj.price_1y,
        "adj_pct_5y": proj.adj_pct_5y,
        "price_5y": proj.price_5y,
        "adj_pct_10y": proj.adj_pct_10y,
        "price_10y": proj.price_10y,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Project prices from Casandra ESG scores.")
    parser.add_argument("--ticker", required=True, help="Stock ticker (e.g., SPG)")
    parser.add_argument("--cik", required=True, help="Company CIK without leading zeros or with (both ok)")
    parser.add_argument("--name", required=True, help="Company name")
    parser.add_argument("--beta_1y", type=float, default=0.10, help="Max 1y proportional move (±)")
    parser.add_argument("--beta_5y", type=float, default=0.20, help="Max 5y proportional move (±)")
    parser.add_argument("--beta_10y", type=float, default=0.30, help="Max 10y proportional move (±)")
    args = parser.parse_args()

    result = run_price_projection(
        ticker=args.ticker,
        cik=str(int(args.cik)),  # normalize CIK like the pipeline expects
        name=args.name,
        beta_1y=args.beta_1y,
        beta_5y=args.beta_5y,
        beta_10y=args.beta_10y,
    )
    print(json.dumps(result, indent=2))
