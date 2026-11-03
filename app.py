import streamlit as st
import pandas as pd
from pathlib import Path
from src.data_loader import load_company, load_peers, load_adjustments
from src.valuation import (
    market_cap, enterprise_value, pe_ratio, ev_multiple,
    dividend_yield, adjusted_earnings_bridge, valuation_summary
)
from src.peer_comparison import peer_statistics

ROOT = Path(__file__).parent
st.set_page_config(page_title="MarketLens | M&S", page_icon="📊", layout="wide")

st.title("MarketLens")
st.caption("Equity valuation & market expectations | Independent research project")

company = load_company(ROOT / "data" / "companies.csv")
peers = load_peers(ROOT / "data" / "peer_groups.csv")
adjustments = load_adjustments(ROOT / "data" / "adjustments.csv")

st.sidebar.header("Company")
st.sidebar.selectbox("Coverage", ["Marks and Spencer Group plc (MKS.L)"], index=0)
st.sidebar.caption("MVP coverage: M&S only")
st.sidebar.header("Market inputs")
price_pence = st.sidebar.number_input("Share price (pence)", min_value=0.0, value=412.0, step=1.0)
price_date = st.sidebar.date_input("Price date", value=pd.Timestamp("2026-10-30").date())
shares_m = st.sidebar.number_input("Diluted shares (millions)", min_value=0.0, value=2065.0, step=1.0,
                                   help="Replace with a verified diluted weighted/period-end share count appropriate to your calculation.")
net_debt_m = st.sidebar.number_input("Net debt incl. lease liabilities (£m)", min_value=0.0, value=2410.0, step=10.0)
dividend_pence = st.sidebar.number_input("Annual dividend per share (pence)", min_value=0.0, value=4.2, step=0.1)

st.info("Illustrative starting inputs: 412p from the supplied Yahoo Finance screenshot dated 30 October 2026; other inputs are editable and must be checked against primary disclosures before publication.")

# Financial inputs: all £m unless stated
st.header("1. Financial inputs")
c1,c2,c3,c4 = st.columns(4)
with c1:
    revenue = st.number_input("Revenue (£m)", min_value=0.0, value=17273.6, step=100.0)
with c2:
    reported_profit = st.number_input("Reported attributable earnings (£m)", min_value=0.0, value=0.0, step=10.0,
                                      help="Enter profit attributable to ordinary shareholders. Do not substitute PBT.")
with c3:
    adjusted_profit = st.number_input("Adjusted attributable earnings (£m)", min_value=0.0, value=0.0, step=10.0)
with c4:
    normalised_profit = st.number_input("Your normalised earnings (£m)", min_value=0.0, value=0.0, step=10.0)

st.caption("The supplied research draft reports FY26 revenue of £17,273.6m, adjusted PBT of £671.4m and statutory PBT of £364.6m. PBT is not the same as attributable net earnings, so the earnings fields deliberately start at zero.")
c5,c6,c7 = st.columns(3)
with c5:
    ebitda = st.number_input("EBITDA (£m)", min_value=0.0, value=0.0, step=10.0)
with c6:
    ebit = st.number_input("EBIT (£m)", min_value=0.0, value=0.0, step=10.0)
with c7:
    fcf = st.number_input("Free cash flow (£m)", value=0.0, step=10.0)

# Adjustment bridge
st.header("2. Accounting adjustment bridge")
st.write("Record each adjustment transparently. The bridge is an analytical view, not an automatic endorsement of management adjustments.")
adj_rows = adjustments.copy()
if adj_rows.empty:
    adj_rows = pd.DataFrame([{"item":"Cyber incident costs (example placeholder)", "amount_gbp_m":0.0, "tax_effect_gbp_m":0.0, "include_in_normalised":False, "analyst_rationale":"Verify recurring/non-recurring nature and tax treatment."}])
edited_adj = st.data_editor(adj_rows, num_rows="dynamic", use_container_width=True, hide_index=True)
bridge = adjusted_earnings_bridge(reported_profit, edited_adj)
st.metric("Normalised earnings from bridge (£m)", f"{bridge:,.1f}" if reported_profit > 0 else "Enter reported earnings first")

st.header("3. Valuation dashboard")
mcap = market_cap(price_pence, shares_m)
ev = enterprise_value(mcap, net_debt_m)
metrics = [
    ("Market capitalisation", f"£{mcap:,.0f}m" if mcap else "—"),
    ("Enterprise value", f"£{ev:,.0f}m" if ev else "—"),
    ("Reported P/E", pe_ratio(mcap, reported_profit)),
    ("Adjusted P/E", pe_ratio(mcap, adjusted_profit)),
    ("Normalised P/E", pe_ratio(mcap, normalised_profit)),
    ("EV/EBITDA", ev_multiple(ev, ebitda)),
    ("EV/EBIT", ev_multiple(ev, ebit)),
    ("Dividend yield", dividend_yield(dividend_pence, price_pence)),
]
cols = st.columns(4)
for i,(label,value) in enumerate(metrics):
    with cols[i % 4]:
        st.metric(label, value if isinstance(value,str) else f"{value:.1f}x" if value is not None else "—")

st.caption(f"Price reference date: {price_date:%d %b %Y} | Currency: GBP | Share price entered in pence.")

st.header("4. Peer comparison")
st.write("Peer data is deliberately editable. Populate current peer price, diluted shares and earnings on a consistent basis before interpreting the comparison.")
peer_df = peers.copy()
if not peer_df.empty:
    st.dataframe(peer_df, use_container_width=True, hide_index=True)
    st.caption("Peer median P/E will calculate when peer earnings and market capitalisation fields are populated.")
    stats = peer_statistics(peer_df)
    a,b,c = st.columns(3)
    a.metric("Peer median P/E", stats.get("median", "—"))
    b.metric("Peer mean P/E", stats.get("mean", "—"))
    c.metric("Peer count", stats.get("count", 0))
else:
    st.warning("No peer data loaded. Add peers to data/peer_groups.csv.")

st.header("5. Scenario analysis")
s1,s2,s3 = st.columns(3)
with s1:
    st.subheader("Bear")
    bear_eps = st.number_input("Bear EPS (£)", min_value=0.0, value=0.20, step=0.01)
    bear_pe = st.number_input("Bear P/E (x)", min_value=0.0, value=8.5, step=0.5)
with s2:
    st.subheader("Base")
    base_eps = st.number_input("Base EPS (£)", min_value=0.0, value=0.30, step=0.01)
    base_pe = st.number_input("Base P/E (x)", min_value=0.0, value=10.5, step=0.5)
with s3:
    st.subheader("Bull")
    bull_eps = st.number_input("Bull EPS (£)", min_value=0.0, value=0.40, step=0.01)
    bull_pe = st.number_input("Bull P/E (x)", min_value=0.0, value=12.0, step=0.5)

scenarios = pd.DataFrame({
    "Scenario":["Bear","Base","Bull"],
    "EPS (£)":[bear_eps,base_eps,bull_eps],
    "P/E (x)":[bear_pe,base_pe,bull_pe],
})
scenarios["Implied price (p)"] = scenarios["EPS (£)"] * scenarios["P/E (x)"] * 100
scenarios["Upside / (downside)"] = scenarios["Implied price (p)"] / price_pence - 1 if price_pence else 0
st.dataframe(scenarios.style.format({"EPS (£)":"£{:.2f}","P/E (x)":"{:.1f}x","Implied price (p)":"{:.1f}p","Upside / (downside)":"{:.1%}"}), use_container_width=True, hide_index=True)

st.header("6. Research controls & disclosures")
st.markdown("""
- **Data status:** Mixed/manual MVP. Values must be independently checked before external publication.
- **Accounting policy:** Reported, management-adjusted and analyst-normalised earnings are separate measures.
- **No automatic investment recommendation:** This dashboard is an analytical tool, not personalised investment advice.
- **Conflicts:** Disclose relevant employment, holdings and other interests. Use only public information; do not enter confidential employer information.
- **Data rights:** Confirm market-data licence and redistribution permissions before publishing a live public feed.
""")
st.download_button("Download current valuation inputs (CSV)",
                   data=pd.DataFrame([{"price_pence":price_pence,"price_date":str(price_date),"shares_m":shares_m,
                                       "revenue_gbp_m":revenue,"reported_earnings_gbp_m":reported_profit,
                                       "adjusted_earnings_gbp_m":adjusted_profit,"normalised_earnings_gbp_m":normalised_profit,
                                       "net_debt_including_leases_gbp_m":net_debt_m}]).to_csv(index=False),
                   file_name="marketlens_mks_inputs.csv", mime="text/csv")
