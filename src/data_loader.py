import pandas as pd

def _load(path, columns):
    try:
        df = pd.read_csv(path)
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=columns)

def load_company(path):
    return _load(path, ["ticker","company","currency","exchange"])

def load_peers(path):
    return _load(path, ["company","ticker","sector","market_cap_gbp_m","earnings_gbp_m"])

def load_adjustments(path):
    df = _load(path, ["item","amount_gbp_m","tax_effect_gbp_m","include_in_normalised","analyst_rationale"])
    if "include_in_normalised" in df.columns:
        df["include_in_normalised"] = df["include_in_normalised"].astype(str).str.lower().isin(["true","1","yes"])
    return df
