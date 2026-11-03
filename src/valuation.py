"""Transparent valuation calculations. Monetary inputs are in GBP millions unless stated."""

def market_cap(price_pence: float, diluted_shares_m: float):
    """Market cap (£m) = price (£/share) * shares (m)."""
    if price_pence <= 0 or diluted_shares_m <= 0:
        return None
    return (price_pence / 100.0) * diluted_shares_m

def enterprise_value(market_cap_m: float, net_debt_m: float):
    if market_cap_m is None:
        return None
    return market_cap_m + net_debt_m

def pe_ratio(market_cap_m: float, earnings_m: float):
    if market_cap_m is None or earnings_m <= 0:
        return None
    return market_cap_m / earnings_m

def ev_multiple(ev_m: float, denominator_m: float):
    if ev_m is None or denominator_m <= 0:
        return None
    return ev_m / denominator_m

def dividend_yield(dividend_pence: float, price_pence: float):
    if price_pence <= 0 or dividend_pence < 0:
        return None
    return f"{dividend_pence / price_pence:.2%}"

def adjusted_earnings_bridge(reported_earnings_m: float, adjustments):
    """Reported earnings + after-tax adjustments selected by analyst."""
    total = reported_earnings_m
    if adjustments is None or len(adjustments) == 0:
        return total
    for _, row in adjustments.iterrows():
        include = row.get("include_in_normalised", False)
        if str(include).lower() in ("true", "1", "yes"):
            amount = float(row.get("amount_gbp_m", 0) or 0)
            tax = float(row.get("tax_effect_gbp_m", 0) or 0)
            total += amount - tax
    return total

def valuation_summary(price_pence, shares_m, reported_earnings_m, adjusted_earnings_m,
                      normalised_earnings_m, net_debt_m=0):
    mc = market_cap(price_pence, shares_m)
    ev = enterprise_value(mc, net_debt_m)
    return {
        "market_cap_gbp_m": mc,
        "enterprise_value_gbp_m": ev,
        "reported_pe": pe_ratio(mc, reported_earnings_m),
        "adjusted_pe": pe_ratio(mc, adjusted_earnings_m),
        "normalised_pe": pe_ratio(mc, normalised_earnings_m),
    }
