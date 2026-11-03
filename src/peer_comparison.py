import pandas as pd

def peer_statistics(df: pd.DataFrame):
    if df is None or df.empty:
        return {"median":"—","mean":"—","count":0}
    required = {"market_cap_gbp_m","earnings_gbp_m"}
    if not required.issubset(df.columns):
        return {"median":"—","mean":"—","count":0}
    x = df.copy()
    x["market_cap_gbp_m"] = pd.to_numeric(x["market_cap_gbp_m"], errors="coerce")
    x["earnings_gbp_m"] = pd.to_numeric(x["earnings_gbp_m"], errors="coerce")
    x = x[(x["market_cap_gbp_m"] > 0) & (x["earnings_gbp_m"] > 0)]
    if x.empty:
        return {"median":"—","mean":"—","count":0}
    x["pe"] = x["market_cap_gbp_m"] / x["earnings_gbp_m"]
    return {"median":f"{x['pe'].median():.1f}x","mean":f"{x['pe'].mean():.1f}x","count":len(x)}
