from casandra.demo_pipeline import score_reit

res = score_reit(
    cik="0000790703",          # Simon Property Group (example CIK without leading zeros)
    name="Simon Property Group",
    ticker="SPG",
    carbon_csv="carbon_inputs.csv",
    max_props=10
)
print(res)
