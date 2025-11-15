'''
Central settings: 
- SEC user-agent string
- timeouts/rate limits
- factor weights (default 33/33/33)
- lookback windows (1y/5y/10y)
'''

# Fill these in before running
SEC_USER_AGENT = "JavierSanjuan ESCP javier.sanjuan@edu.escp.eu"
REQUEST_TIMEOUT = 30 # This tells Python to stop waiting after 30 seconds if a website doesn’t respond. (Prevents your code from freezing forever on a slow connection.)
REQUEST_SLEEP = 2  # This adds a 0.6-second pause between requests to the SEC. (Prevents sending too many requests too fas

# Metric weights (sum to 1.0). Keep them configurable.
WEIGHTS = {
    "climate": 1/3,
    "carbon":  1/3,
    "gov":     1/3,
}

# Rolling windows for governance sentiment (in days)
WINDOWS = {"1y": 365, "5y": 5*365, "10y": 10*365}

# Optional: Google News RSS query templates per ticker/name
NEWS_QUERIES = [
    "{name} REIT controversy",
    "{name} governance",
    "{name} lawsuit",
    "{name} ESG",
]
