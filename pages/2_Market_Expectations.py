"""MarketLens: standalone Streamlit expectations and multiple-compression research page.
Upload this file to pages/ in the existing Streamlit repository. No other dependencies.
"""
import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="MarketLens | Market Expectations", layout="wide")
st.title("MarketLens · Market Expectations & Multiple Compression")
st.caption("Independent research workbench · Manual, illustrative inputs · No live market data or investment advice")

with st.sidebar:
    st.header("Security & valuation date")
    ticker = st.text_input("Ticker", "NVDA").strip().upper() or "NVDA"
    currency = st.text_input("Currency", "USD").strip().upper() or "USD"
    price = st.number_input("Current share price", min_value=0.01, value=200.0, step=1.0)
    shares = st.number_input("Diluted shares outstanding (millions)", min_value=0.01, value=24500.0, step=100.0)
    net_debt = st.number_input("Net debt (cash is negative; millions)", value=-20000.0, step=1000.0)
    eps0 = st.number_input("Base-year diluted EPS", min_value=0.001, value=4.0, step=0.1, format="%.3f")
    annual_dividend = st.number_input("Annual dividends per share", min_value=0.0, value=0.0, step=0.05)
    st.caption("Replace ALL defaults with dated, verified financials. Use consistent diluted share counts and earnings definitions.")

market_cap = price * shares  # millions
pe0 = price / eps0
st.subheader("1 · Starting valuation")
a,b,c,d = st.columns(4)
a.metric("Market capitalisation", f"{market_cap/1000:,.2f} bn {currency}")
b.metric("Trailing/base P/E", f"{pe0:.1f}x")
c.metric("Base earnings", f"{eps0*shares/1000:,.2f} bn {currency}")
d.metric("Enterprise value", f"{(market_cap+net_debt)/1000:,.2f} bn {currency}")
st.info("A lower forward P/E at today's price is not itself a share-price forecast. A future exit P/E must be paired with future earnings to estimate a future price.")

st.subheader("2 · Five-year EPS forecast and multiple-compression sensitivity")
left,right = st.columns(2)
with left:
    eps_growth = st.number_input("Initial annual EPS growth assumption (%)", min_value=-90.0, max_value=300.0, value=25.0, step=1.0)
with right:
    exit_pe = st.number_input("Base-case year-5 exit P/E", min_value=1.0, max_value=300.0, value=25.0, step=1.0)

editable = pd.DataFrame({"Year": [f"FY+{i}" for i in range(1,6)], "EPS growth (%)": [eps_growth]*5})
growth_table = st.data_editor(editable, hide_index=True, use_container_width=True, disabled=["Year"], key="eps_growth_editor")
eps = eps0
rows=[]
for idx, row in growth_table.iterrows():
    g = float(row["EPS growth (%)"])
    if not math.isfinite(g) or g <= -100:
        st.error("Each EPS growth input must be a finite number greater than -100%.")
        st.stop()
    eps *= (1+g/100)
    rows.append({"Year":f"FY+{idx+1}", "EPS":eps, "Earnings (mn)":eps*shares,
                 "P/E at unchanged price":price/eps, "Price at base exit P/E":eps*exit_pe})
forecast = pd.DataFrame(rows)
st.dataframe(forecast.style.format({"EPS":"{:,.3f}", "Earnings (mn)":"{:,.1f}", "P/E at unchanged price":"{:.1f}x", "Price at base exit P/E":"{:,.2f}"}), hide_index=True, use_container_width=True)
st.download_button("Download EPS forecast", forecast.to_csv(index=False), "marketlens_eps_forecast.csv", "text/csv")

st.markdown("**Year-5 implied price sensitivity (exit P/E × forecast EPS)**")
pe_range = [max(1.,exit_pe*factor) for factor in (0.6,0.8,1.0,1.2,1.4)]
eps_range = [max(0.001,eps*factor) for factor in (0.7,0.85,1.0,1.15,1.3)]
sensitivity = pd.DataFrame({f"EPS {v:.2f}":[m*v for m in pe_range] for v in eps_range}, index=[f"{m:.1f}x" for m in pe_range])
st.dataframe(sensitivity.style.format("{:,.2f}"), use_container_width=True)

st.subheader("3 · Valuation decomposition")
price5 = eps*exit_pe
price_return = price5/price-1
annualised = (price5/price)**(1/5)-1
cum_div = annual_dividend*5
price_plus_div_return = (price5+cum_div)/price-1
st.write("Share-price change = (EPS growth factor × P/E change factor) − 1. This is a multiplicative decomposition, not an additive attribution.")
q1,q2,q3,q4 = st.columns(4)
q1.metric("Five-year EPS change", f"{(eps/eps0-1)*100:+.1f}%")
q2.metric("Exit multiple change", f"{(exit_pe/pe0-1)*100:+.1f}%")
q3.metric("Five-year price return", f"{price_return*100:+.1f}%")
q4.metric("Price CAGR", f"{annualised*100:+.1f}%")
st.caption(f"Undiscounted cumulative dividends assumed constant: {cum_div:.2f} {currency}/share; total simple holding-period return including these dividends: {price_plus_div_return*100:+.1f}%. No dividend reinvestment, buybacks, taxes or dilution modelled.")
st.write(f"At an exit P/E of **{exit_pe:.1f}x**, EPS must reach **{price/exit_pe:.3f}** to preserve today's share price. Required five-year EPS CAGR: **{((price/exit_pe/eps0)**(1/5)-1)*100:.1f}%**.")

st.subheader("4 · Reverse DCF: what free-cash-flow growth does today's price imply?")
st.caption("Simplified enterprise FCFF DCF: 5 years of annual growth from base FCFF, terminal growth thereafter, year-end discounting, and net debt adjustment. Growth and terminal assumptions must be economically plausible.")
r1,r2,r3 = st.columns(3)
with r1: fcf0 = st.number_input(f"Base FCFF (millions {currency})", min_value=0.01, value=100000.0, step=1000.0)
with r2: wacc = st.number_input("WACC (%)", min_value=0.1, max_value=60.0, value=10.0, step=0.25)/100
with r3: terminal_g = st.number_input("Terminal growth (%)", min_value=-10.0, max_value=30.0, value=3.0, step=0.25)/100
if terminal_g >= wacc:
    st.error("Terminal growth must be lower than WACC for a perpetuity-growth DCF.")
else:
    def enterprise_dcf(g):
        fcf=fcf0
        pv=0.0
        for year in range(1,6):
            fcf *= (1+g)
            pv += fcf/(1+wacc)**year
        terminal = fcf*(1+terminal_g)/(wacc-terminal_g)
        return pv+terminal/(1+wacc)**5
    target_ev = market_cap + net_debt
    lo,hi=-0.95,3.0
    val_lo,val_hi=enterprise_dcf(lo),enterprise_dcf(hi)
    if not (val_lo<=target_ev<=val_hi):
        st.warning("No implied growth solution within the model's search range (−95% to +300% annually). Check FCFF, capital structure and discount assumptions.")
    else:
        for _ in range(110):
            mid=(lo+hi)/2
            if enterprise_dcf(mid)<target_ev: lo=mid
            else: hi=mid
        implied=(lo+hi)/2
        u,v=st.columns(2)
        u.metric("Market-implied FCFF CAGR (5 years)", f"{implied*100:.2f}%")
        v.metric("Implied year-5 FCFF", f"{fcf0*(1+implied)**5/1000:,.2f} bn {currency}")
        analyst_g=st.number_input("Your expected FCFF CAGR (%)", min_value=-90.0, max_value=300.0, value=20.0, step=1.0)/100
        your_ev=enterprise_dcf(analyst_g)
        your_equity=your_ev-net_debt
        your_price=your_equity/shares
        st.metric("Your DCF implied share value", f"{your_price:,.2f} {currency}", delta=f"{(your_price/price-1)*100:+.1f}% vs current price")
        st.caption("FCFF is enterprise cash flow; EV is converted to equity value by subtracting net debt. Negative equity values or extreme growth assumptions indicate the simplified model may be inappropriate.")

st.subheader("5 · Your forecasts vs consensus expectations")
st.caption("Enter a dated analyst-consensus EPS estimate manually. Blank/zero means unavailable; MarketLens does not fetch consensus estimates.")
consensus = st.number_input("Year-5 consensus EPS (0 = unavailable)", min_value=0.0, value=0.0, step=0.1, format="%.3f")
if consensus>0:
    gap=eps/consensus-1
    st.metric("Your EPS vs consensus", f"{gap*100:+.1f}%")
    st.write(f"Your year-5 EPS: **{eps:.3f}** · Consensus: **{consensus:.3f}**. The gap is an earnings-estimate difference, not automatically a price-return prediction.")
else:
    st.write("Consensus not entered — no consensus comparison is shown.")

st.subheader("6 · PEG ratio (supporting diagnostic)")
forward_eps = float(forecast.iloc[0]["EPS"])
forward_pe = price/forward_eps
peg_growth = st.number_input("Expected annual EPS growth for PEG (%)", min_value=0.01, value=25.0, step=1.0)
peg=forward_pe/peg_growth
st.metric("Forward P/E / growth rate (PEG)", f"{peg:.2f}x")
st.caption("PEG uses the conventional percentage-number growth rate (e.g., 25 rather than 0.25). It is unreliable for cyclical earnings, short-lived growth and non-comparable accounting.")

st.subheader("7 · Bear / base / bull expected returns")
st.caption("Each scenario independently specifies year-5 EPS and exit P/E. Probabilities must total 100%. Annual dividends assumed constant; outcomes are illustrative, not calibrated probabilities.")
default_scenarios=pd.DataFrame({
    "Scenario":["Bear","Base","Bull"],
    "EPS factor vs your FY+5":[0.70,1.00,1.30],
    "Exit P/E":[max(1.,exit_pe*0.65),exit_pe,exit_pe*1.30],
    "Probability (%)":[25.,50.,25.]
})
scenarios=st.data_editor(default_scenarios,hide_index=True,disabled=["Scenario"],use_container_width=True,key="scenario_editor")
try:
    probabilities=[float(v) for v in scenarios["Probability (%)"]]
    factors=[float(v) for v in scenarios["EPS factor vs your FY+5"]]
    multiples=[float(v) for v in scenarios["Exit P/E"]]
    if any(not math.isfinite(x) for x in probabilities+factors+multiples) or any(x<0 for x in probabilities) or any(x<=0 for x in factors+multiples) or abs(sum(probabilities)-100)>0.01:
        st.warning("Probabilities must be non-negative and sum to 100%; EPS factors and exit P/E must be positive.")
    else:
        scenario_rows=[]
        for name,factor,mult,prob in zip(scenarios["Scenario"],factors,multiples,probabilities):
            terminal_price=eps*factor*mult
            total_return=(terminal_price+cum_div)/price-1
            scenario_rows.append({"Scenario":name,"Year-5 EPS":eps*factor,"Exit P/E":mult,"Year-5 price":terminal_price,"5Y total return (%)":total_return*100,"Annualised total return (%)":((terminal_price+cum_div)/price)**0.2*100-100,"Probability (%)":prob})
        outcomes=pd.DataFrame(scenario_rows)
        st.dataframe(outcomes.style.format({"Year-5 EPS":"{:.3f}","Exit P/E":"{:.1f}x","Year-5 price":"{:,.2f}","5Y total return (%)":"{:+.1f}%","Annualised total return (%)":"{:+.1f}%","Probability (%)":"{:.1f}%"}),hide_index=True,use_container_width=True)
        expected_terminal=sum(row["Year-5 price"]*row["Probability (%)"]/100 for row in scenario_rows)
        expected_return=(expected_terminal+cum_div)/price-1
        st.metric("Probability-weighted 5Y total return",f"{expected_return*100:+.1f}%")
        st.caption("Expected annualised return is not the weighted average of scenario annualised returns. These probabilities are user assumptions.")
        st.download_button("Download scenario table",outcomes.to_csv(index=False),"marketlens_scenarios.csv","text/csv")
except (ValueError, TypeError, OverflowError):
    st.warning("Enter valid numeric values in the scenario table.")

st.divider()
st.caption("Research controls: verify fiscal-year definitions, forecast date, adjusted vs GAAP EPS, split-adjusted shares, net debt, FCFF, WACC and terminal growth. Model outputs are not trading signals.")
