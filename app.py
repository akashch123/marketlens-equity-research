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
    peer_df = st.data_editor(
        peer_df, use_container_width=True, hide_index=True,
        num_rows="dynamic", key="editable_peer_comparison",
        column_config={
            "market_cap_gbp_m": st.column_config.NumberColumn("Market cap (£m)", min_value=0.0, format="%.2f"),
            "earnings_gbp_m": st.column_config.NumberColumn("Net earnings (£m)", format="%.2f"),
        },
    )
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

# Extended five-year research models
from src.forecast import capm, wacc, forecast, dcf, economic_profit

st.header('7. Five-year forecast & intrinsic valuation')
st.caption('Analyst assumptions are illustrative starting points, not management guidance. Financial figures are £m; rates are annual.')
with st.expander('CAPM and WACC assumptions', expanded=True):
    k1,k2,k3,k4 = st.columns(4)
    rf=k1.number_input('Risk-free rate (%)',value=4.0,step=0.25)/100
    beta=k2.number_input('Levered equity beta',value=1.0,step=0.1)
    erp=k3.number_input('Equity risk premium (%)',value=5.5,step=0.25)/100
    crp=k4.number_input('Country risk premium (%)',value=0.0,step=0.25)/100
    k5,k6,k7 = st.columns(3)
    debt_cost=k5.number_input('Pre-tax cost of debt (%)',value=5.0,step=0.25)/100
    tax=k6.number_input('Forecast cash tax rate (%)',value=25.0,step=0.5)/100
    debt_for_wacc=k7.number_input('Interest-bearing debt for WACC (£m)',min_value=0.0,value=2410.0,step=10.0,
                                    help='Verify lease/debt definition and avoid double counting net debt.')
    ke=capm(rf,beta,erp,crp)
    kw=wacc(ke,debt_cost,tax,mcap or 0,debt_for_wacc) if mcap else None
    a,b=st.columns(2)
    a.metric('CAPM cost of equity',f'{ke:.2%}')
    b.metric('Weighted average cost of capital',f'{kw:.2%}' if kw is not None else '—')

st.subheader('Five-year operating assumptions')
initial_nwc=st.number_input('Opening operating net working capital (£m)',value=0.0,step=10.0,
                             help='Enter the actual opening NWC for correct first-year cash flow.')
assumptions=pd.DataFrame({
    'Year':[f'FY+{i}' for i in range(1,6)],
    'Revenue growth %':[4.5]*5,
    'EBIT margin %':[5.0,5.3,5.6,5.9,6.2],
    'D&A / sales %':[3.0]*5,
    'CapEx / sales %':[4.0]*5,
    'Operating NWC / sales %':[1.0]*5,
})
assumptions=st.data_editor(assumptions,hide_index=True,use_container_width=True,num_rows='fixed',key='forecast_assumptions')
try:
    fc=forecast(revenue,
        (assumptions['Revenue growth %']/100).tolist(),
        (assumptions['EBIT margin %']/100).tolist(),tax,
        (assumptions['D&A / sales %']/100).tolist(),
        (assumptions['CapEx / sales %']/100).tolist(),
        (assumptions['Operating NWC / sales %']/100).tolist(),initial_nwc)
    st.dataframe(fc.style.format({col:'{:,.1f}' for col in fc.columns if col!='Year'}),use_container_width=True,hide_index=True)
    st.line_chart(fc.set_index('Year')[['Revenue','EBIT','FCFF']])
    st.download_button('Download five-year forecast CSV',fc.to_csv(index=False),file_name='marketlens_mks_forecast.csv')
    st.subheader('Discounted cash flow (FCFF)')
    tg=st.number_input('Terminal perpetual growth (%)',value=2.0,step=0.25)/100
    discount_override=st.checkbox('Override WACC for valuation',value=False)
    valuation_wacc=st.number_input('Valuation discount rate (%)',value=9.0,step=0.25)/100 if discount_override else kw
    if valuation_wacc is not None:
        result=dcf(fc['FCFF'].tolist(),valuation_wacc,tg,net_debt_m,shares_m)
        d1,d2,d3,d4=st.columns(4)
        d1.metric('DCF enterprise value',f"£{result['enterprise_value']:,.0f}m")
        d2.metric('DCF equity value',f"£{result['equity_value']:,.0f}m")
        d3.metric('DCF implied price',f"{result['price_pence']:,.1f}p")
        d4.metric('Terminal share of EV',f"{result['terminal_weight']:.1%}" if result['terminal_weight'] is not None else '—')
        st.caption('EV-to-equity bridge subtracts net debt as entered in the sidebar. Confirm treatment of leases, pensions, minority interests, cash and non-operating assets.')
        st.subheader('DCF sensitivity: implied price (pence)')
        sensitivities=[]
        for rate in [valuation_wacc-.01,valuation_wacc-.005,valuation_wacc,valuation_wacc+.005,valuation_wacc+.01]:
            row={'WACC':f'{rate:.2%}'}
            for g in [tg-.005,tg,tg+.005]:
                try: row[f'g={g:.2%}']=round(dcf(fc['FCFF'].tolist(),rate,g,net_debt_m,shares_m)['price_pence'],1)
                except ValueError: row[f'g={g:.2%}']=None
            sensitivities.append(row)
        st.dataframe(pd.DataFrame(sensitivities),hide_index=True,use_container_width=True)
        st.subheader('Economic Returns Model (ROIC vs WACC)')
        opening_ic=st.number_input('Opening invested capital (£m)',min_value=1.0,value=8000.0,step=100.0,
                                   help='Enter verified operating invested capital; default is illustrative.')
        reinvestment=(fc['CapEx']-fc['D&A']+fc['Change in NWC']).tolist()
        er=economic_profit(fc['NOPAT'].tolist(),opening_ic,reinvestment,valuation_wacc,tg,net_debt_m,shares_m)
        st.dataframe(er['years'].style.format({'opening_capital':'{:,.1f}','roic':'{:.1%}',
                          'economic_profit':'{:,.1f}','pv_ep':'{:,.1f}'}),hide_index=True,use_container_width=True)
        e1,e2=st.columns(2)
        e1.metric('Economic-profit implied price',f"{er['price_pence']:,.1f}p")
        e2.metric('DCF vs economic-profit difference',f"{er['price_pence']-result['price_pence']:+,.1f}p")
        st.warning('Economic-profit terminal value here grows Year-5 economic profit perpetually. This simplifying assumption need not reconcile with the FCFF terminal value. Treat differences as a modelling check, not independent confirmation.')
except (ValueError, TypeError, ZeroDivisionError) as exc:
    st.error(f'Check forecast inputs: {exc}')
