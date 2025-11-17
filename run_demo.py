from casandra.demo_pipeline import score_reit

CARBON_CSV = "carbon_inputs.csv"

res = score_reit(
    cik="0000899689",
    name="Vornado Realty Trust",
    ticker="VNO",
    carbon_csv=str(CARBON_CSV)
)

print(res)
