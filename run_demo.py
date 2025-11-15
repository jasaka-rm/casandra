from casandra.demo_pipeline import score_reit

res = score_reit(
    cik="0000899689",          
    name="Vornado Realty Trust",
    ticker="VRT"
)
print(res)
