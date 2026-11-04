"""MarketLens universal, manually sourced equity valuation workspace.
Upload this file into the GitHub repository's pages/ directory.
All monetary financial statement inputs are in MILLIONS of the chosen currency.
"""
import io
import json
from datetime import date

import pandas as pd
import streamlit as st

st.set_page_config(page_title="MarketLens | Universal Calculator", page_icon="🌐", layout="wide")
st.title("🌐 Universal Equity Research Calculator")
st.caption("Company-independent research workspace • Manual, source-verified inputs • All financial totals in millions")

with st.sidebar:
    st.header("Research identity")
    ticker = st.text_input("Ticker / identifier", value="NEW", help="Use a unique identifier for each company, e.g. TM, NVDA, MKS.L")
    company = st.text_input("Company", value="New company")
    currency = st.selectbox("Reporting / valuation currency", ["USD", "GBP", "JPY", "EUR", "INR", "CAD", "AUD", "CHF", "CNY", "Other"])
    price_date = st.date_input("Share price observation date", value=date.today())
    financial_period = st.text_input("Financial reporting period", value="FY2025")
    source = st.text_input("Primary source / report URL", value="")
    st.warning("Changing the ticker does not automatically load company data. Clear or replace every field when switching companies. Never mix currencies or entities.")

st.info("Enter share price in full currency units (e.g. GBP 4.12, **not** 412 pence). Enter financial totals and share count in **millions**. For JPY, use ¥ per share and ¥ millions. No automatic FX conversion or live financial feed.")

with st.expander("1. Company inputs — price, capital structure and earnings", expanded=True):
    a,b,c,d = st.columns(4)
    with a:
        price = st.number_input(f"Share price ({currency}/share)", min_value=0.0, value=0.0, step=1.0, format="%.4f")
        shares = st.number_input("Shares outstanding (millions)", min_value=0.0, value=0.0, step=1.0)
        dividend = st.number_input(f"Annual dividend ({currency}/share)", min_value=0.0, value=0.0, step=0.1)
    with b:
        debt = st.number_input(f"Interest-bearing debt ({currency}m)", min_value=0.0, value=0.0)
        cash = st.number_input(f"Cash & equivalents ({currency}m)", min_value=0.0, value=0.0)
        lease = st.number_input(f"Lease liabilities, if separate ({currency}m)", min_value=0.0, value=0.0)
    with c:
        reported = st.number_input(f"Reported attributable earnings ({currency}m)", value=0.0)
        adjusted = st.number_input(f"Adjusted attributable earnings ({currency}m)", value=0.0)
        normalised = st.number_input(f"Analyst normalised earnings ({currency}m)", value=0.0)
    with d:
        revenue = st.number_input(f"Revenue ({currency}m)", min_value=0.0, value=0.0)
        ebit = st.number_input(f"EBIT ({currency}m)", value=0.0)
        ebitda = st.number_input(f"EBITDA ({currency}m)", value=0.0)
        minorities = st.number_input(f"Non-controlling interests ({currency}m)", min_value=0.0, value=0.0)
        other_claims = st.number_input(f"Other EV claims / preferred equity ({currency}m)", min_value=0.0, value=0.0)
    st.caption("Debt should exclude leases if entered separately. EV/EBITDA must use consistent lease accounting. Use attributable net profit, not PBT, for equity P/E.")

mcap = price * shares
net_debt = debt + lease - cash
enterprise = mcap + net_debt + minorities + other_claims

def ratio(n, d):
    return n/d if d > 0 else None

def fmt(v, suffix="x"):
    return f"{v:,.2f}{suffix}" if v is not None else "—"

st.header("2. Valuation dashboard")
c = st.columns(4)
c[0].metric("Market cap", f"{mcap:,.2f} {currency}m")
c[1].metric("Enterprise value", f"{enterprise:,.2f} {currency}m")
c[2].metric("Reported P/E", fmt(ratio(mcap, reported)))
c[3].metric("Adjusted P/E", fmt(ratio(mcap, adjusted)))
c = st.columns(4)
c[0].metric("Normalised P/E", fmt(ratio(mcap, normalised)))
c[1].metric("EV / EBITDA", fmt(ratio(enterprise, ebitda)))
c[2].metric("EV / EBIT", fmt(ratio(enterprise, ebit)))
c[3].metric("Dividend yield", fmt(100 * dividend / price if price > 0 else None, "%"))

issues = []
if not ticker.strip() or not company.strip(): issues.append("Identify the company and ticker.")
if price <= 0 or shares <= 0: issues.append("A positive price and share count are required for meaningful valuation.")
if min(reported, adjusted, normalised) < 0: issues.append("Negative earnings: P/E is not meaningful; use other methods.")
if reported == 0: issues.append("Reported attributable earnings are missing or zero; do not interpret reported P/E.")
if adjusted == 0: issues.append("Adjusted earnings are missing or zero.")
if normalised == 0: issues.append("Normalised earnings are missing or zero.")
if revenue > 0 and abs(reported) > revenue: issues.append("Attributable earnings exceed revenue: check units, entity, period and whether revenue/earnings were swapped.")
if revenue > 0 and abs(ebit) > revenue: issues.append("Absolute EBIT exceeds revenue: verify definitions and inputs.")
if not source.strip(): issues.append("Add a primary source link for auditability.")
if enterprise < 0: issues.append("Enterprise value is negative: check cash, debt, minority interest and share count.")
with st.expander(f"Input quality checks ({len(issues)} flags)", expanded=bool(issues)):
    if issues:
        for issue in issues: st.warning(issue)
    else: st.success("Basic plausibility checks passed. This does not verify the numbers or accounting definitions.")
    st.caption("Company identity, currency, share-class, fiscal period and filing consistency still require analyst verification.")

st.header("3. CAPM, beta and cost of capital")
with st.expander("Beta relevering and WACC", expanded=False):
    x,y,z = st.columns(3)
    with x:
        unlevered_beta = st.number_input("Unlevered beta", min_value=0.0, value=1.0, step=0.05)
        tax = st.number_input("Marginal tax rate (%)", min_value=0.0, max_value=100.0, value=25.0, step=0.5)/100
        equity_for_beta = st.number_input(f"Market value of equity for beta ({currency}m; 0 = calculated)", min_value=0.0, value=0.0)
    with y:
        risk_free = st.number_input("Risk-free rate (%)", value=4.0, step=0.25)/100
        erp = st.number_input("Equity risk premium (%)", min_value=0.0, value=5.0, step=0.25)/100
        extra_premium = st.number_input("Country / size premium (%)", value=0.0, step=0.25)/100
    with z:
        cost_debt = st.number_input("Pre-tax cost of debt (%)", min_value=0.0, value=5.0, step=0.25)/100
        beta_debt = st.number_input("Debt beta (assumed zero in Hamada formula)", min_value=0.0, value=0.0, step=0.05, help="If debt beta is material, simple Hamada relevering is not sufficient.")
    eq_mv = equity_for_beta or mcap
    debt_mv = debt + lease
    d_e = debt_mv / eq_mv if eq_mv > 0 else None
    levered_beta = unlevered_beta * (1 + (1-tax)*d_e) if d_e is not None else None
    cost_equity = risk_free + (levered_beta or 0)*erp + extra_premium if levered_beta is not None else None
    wacc = ((eq_mv/(eq_mv+debt_mv))*cost_equity + (debt_mv/(eq_mv+debt_mv))*cost_debt*(1-tax)) if cost_equity is not None and eq_mv+debt_mv>0 else None
    cc = st.columns(4)
    cc[0].metric("Debt / equity", fmt(d_e))
    cc[1].metric("Levered beta", fmt(levered_beta, ""))
    cc[2].metric("Cost of equity (CAPM)", fmt(100*cost_equity if cost_equity is not None else None, "%"))
    cc[3].metric("WACC", fmt(100*wacc if wacc is not None else None, "%"))
    st.caption("Hamada beta = unlevered beta × [1 + (1 − tax) × D/E]. Assumes debt beta ≈ 0. Use market-value leverage and sector-appropriate tax and risk-free rates.")
    if beta_debt > 0: st.warning("Nonzero debt beta entered: displayed Hamada beta does not incorporate it. Consider a full asset-beta decomposition.")

st.header("4. Five-year forecast and discounted cash flow")
with st.expander("Operating forecasts, FCFF and terminal value", expanded=False):
    f1,f2,f3 = st.columns(3)
    with f1:
        growth = st.number_input("Annual revenue growth (%)", value=8.0, step=1.0)/100
        operating_margin = st.number_input("Forecast EBIT margin (%)", value=15.0, step=1.0)/100
        forecast_tax = st.number_input("Forecast cash tax on EBIT (%)", min_value=0.0, max_value=100.0, value=25.0)/100
    with f2:
        da_pct = st.number_input("D&A as % of revenue", min_value=0.0, value=4.0)/100
        capex_pct = st.number_input("CAPEX as % of revenue", min_value=0.0, value=6.0)/100
        nwc_pct = st.number_input("Increase in operating NWC as % of incremental revenue", value=10.0)/100
    with f3:
        terminal_growth = st.number_input("Terminal growth (%)", value=2.5, step=0.25)/100
        discount_override = st.number_input("Discount rate override (%) (0 = WACC)", min_value=0.0, value=0.0)/100
        net_debt_override = st.number_input(f"Equity bridge adjustment ({currency}m; other non-operating assets minus other claims)", value=0.0)
    discount = discount_override or wacc
    forecast = []
    previous_rev = revenue
    for year in range(1,6):
        sales = previous_rev * (1+growth)
        op = sales * operating_margin
        nopat = op*(1-forecast_tax)
        da = sales * da_pct
        capex = sales * capex_pct
        dnwc = (sales-previous_rev)*nwc_pct
        fcff = nopat + da - capex - dnwc
        forecast.append({"Year": f"Y{year}", "Revenue": sales, "EBIT": op, "NOPAT": nopat, "D&A": da, "CAPEX": capex, "ΔNWC": dnwc, "FCFF": fcff})
        previous_rev = sales
    forecast_df = pd.DataFrame(forecast)
    st.dataframe(forecast_df.style.format({col:"{:,.2f}" for col in forecast_df.columns if col!="Year"}), use_container_width=True, hide_index=True)
    st.line_chart(forecast_df.set_index("Year")[["Revenue","EBIT","FCFF"]])
    if revenue <= 0 or shares <= 0:
        st.warning("Enter positive current revenue and shares outstanding to calculate DCF value per share.")
    elif discount is None:
        st.warning("Enter capital structure and CAPM inputs or set a discount rate override.")
    elif discount <= terminal_growth:
        st.error("Discount rate must exceed terminal growth for a Gordon-growth terminal value.")
    else:
        pv_fcff = sum(row["FCFF"] / ((1+discount)**i) for i,row in enumerate(forecast,1))
        terminal = forecast[-1]["FCFF"]*(1+terminal_growth)/(discount-terminal_growth)
        pv_terminal = terminal/(1+discount)**5
        dcf_ev = pv_fcff+pv_terminal
        dcf_equity = dcf_ev-net_debt-minorities-other_claims+net_debt_override
        dcf_price = dcf_equity/shares
        dc = st.columns(4)
        dc[0].metric("PV of forecast FCFF", f"{pv_fcff:,.1f} {currency}m")
        dc[1].metric("PV of terminal value", f"{pv_terminal:,.1f} {currency}m")
        dc[2].metric("DCF equity value", f"{dcf_equity:,.1f} {currency}m")
        dc[3].metric("DCF / share", f"{dcf_price:,.2f} {currency}")
        st.caption(f"Terminal value is {pv_terminal/(dcf_ev)*100:.1f}% of enterprise value" if dcf_ev else "")
        st.warning("DCF is an illustrative constant-growth, constant-margin model. Refine year-by-year assumptions, working capital, terminal economics and sector-specific accounting before publishing.")

st.header("5. Reverse target-price calculator")
with st.expander("Price ↔ earnings ↔ forward P/E", expanded=True):
    a,b,c,d = st.columns(4)
    with a: target_price = st.number_input(f"Target share price ({currency})", min_value=0.0, value=0.0, step=1.0)
    with b: forecast_net = st.number_input(f"Forecast attributable net profit ({currency}m)", value=0.0)
    with c: target_pe = st.number_input("Assumed forward P/E (x)", min_value=0.01, value=20.0, step=1.0)
    with d: future_shares = st.number_input("Forecast diluted shares (millions; 0 = current)", min_value=0.0, value=0.0)
    effective_shares = future_shares or shares
    target_mcap = target_price * effective_shares
    implied_pe = ratio(target_mcap, forecast_net)
    required_earnings = target_mcap / target_pe if target_pe > 0 else None
    eps = forecast_net / effective_shares if effective_shares > 0 else None
    pe_implied_price = eps*target_pe if eps is not None else None
    metrics = st.columns(4)
    metrics[0].metric("Implied P/E at target", fmt(implied_pe))
    metrics[1].metric("Required earnings at assumed P/E", f"{required_earnings:,.2f} {currency}m" if required_earnings is not None else "—")
    metrics[2].metric("Forecast EPS", f"{eps:,.3f} {currency}" if eps is not None else "—")
    metrics[3].metric("Target market cap", f"{target_mcap:,.2f} {currency}m")
    st.metric("Share price implied by forecast earnings × chosen P/E", f"{pe_implied_price:,.2f} {currency}" if pe_implied_price is not None else "—")
    if price > 0 and target_price > 0:
        st.caption(f"Upside/downside from entered price: {(target_price/price-1)*100:+.1f}%")
    st.caption("A target P/E is an analyst assumption to justify using peers, growth, ROIC, risk and history—not a value mechanically determined by earnings.")

st.header("6. Economic returns / value creation")
with st.expander("ROIC spread and economic profit", expanded=False):
    invested_capital = st.number_input(f"Average invested capital ({currency}m)", min_value=0.0, value=0.0)
    nopat_input = st.number_input(f"NOPAT ({currency}m; enter directly)", value=0.0)
    roic = nopat_input / invested_capital if invested_capital > 0 else None
    spread = roic-wacc if roic is not None and wacc is not None else None
    ep = nopat_input - invested_capital*wacc if wacc is not None and invested_capital > 0 else None
    c = st.columns(3)
    c[0].metric("ROIC", fmt(roic*100 if roic is not None else None, "%"))
    c[1].metric("ROIC − WACC", fmt(spread*100 if spread is not None else None, " pp"))
    c[2].metric("Economic profit", f"{ep:,.2f} {currency}m" if ep is not None else "—")
    st.caption("Economic profit = NOPAT − WACC × invested capital. Positive economic profit indicates value creation on the chosen accounting basis; this is not a full residual-income valuation.")

st.header("7. Export research snapshot")
snapshot = {
    "company": company, "ticker": ticker, "currency": currency,
    "price_date": str(price_date), "financial_period": financial_period, "primary_source": source,
    "inputs": {"price_per_share": price, "shares_m": shares, "dividend_per_share": dividend,
               "debt_m": debt, "lease_liabilities_m": lease, "cash_m": cash,
               "reported_attributable_earnings_m": reported, "adjusted_attributable_earnings_m": adjusted,
               "normalised_earnings_m": normalised, "revenue_m": revenue, "ebit_m": ebit, "ebitda_m": ebitda},
    "metrics": {"market_cap_m": mcap, "enterprise_value_m": enterprise,
                "reported_pe": ratio(mcap, reported), "adjusted_pe": ratio(mcap, adjusted),
                "normalised_pe": ratio(mcap, normalised), "levered_beta": levered_beta,
                "cost_of_equity": cost_equity, "wacc": wacc,
                "reverse_target_implied_pe": implied_pe, "reverse_target_required_earnings_m": required_earnings},
    "quality_flags": issues,
    "forecast_assumptions": {"revenue_growth": growth, "ebit_margin": operating_margin,
                             "cash_tax": forecast_tax, "terminal_growth": terminal_growth},
    "five_year_forecast": forecast,
}
file_base = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in ticker) or "company"
st.download_button("Download research inputs + calculations (JSON)", data=json.dumps(snapshot, indent=2), file_name=f"marketlens_{file_base}_{price_date}.json", mime="application/json")
st.download_button("Download five-year forecast (CSV)", data=forecast_df.to_csv(index=False), file_name=f"marketlens_{file_base}_forecast.csv", mime="text/csv")
st.caption("Research tool only. Outputs are not investment advice, and all input figures require independent verification.")
