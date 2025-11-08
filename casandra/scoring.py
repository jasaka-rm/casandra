'''
Combines the three factor scores using the weights from config.py to one ESG-Adjusted Distress score (0–100).
'''

from typing import Dict
from .config import WEIGHTS

def combine_scores(climate_score: float, carbon_score: float, gov_score: float) -> float:
    """
    All inputs on 0–100 scale (higher = WORSE).
    Output: 0–100 ESG-Adjusted Distress (higher = worse).
    """
    w = WEIGHTS
    final = w["climate"]*climate_score + w["carbon"]*carbon_score + w["gov"]*gov_score
    return round(final, 2)
