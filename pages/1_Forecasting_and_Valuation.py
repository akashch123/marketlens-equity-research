"""Standalone additive Streamlit page for MarketLens. No edits to app.py needed."""
import pandas as pd
import streamlit as st

st.set_page_config(page_title='MarketLens | Forecast & Valuation', layout='wide')
st.title('MarketLens · 5-Year Forecast & Valuation')
st.caption('Research sandbox | All starting assumptions are illustrative, not verified forecasts.')

with st.sidebar:
    st.header('Company & market')
    price_p = st.number_input('Share price (p)', min_value=0.01, value=412.0)
    shares_m = st.number_input('Diluted shares (million)', min_value=0.01, value=2065.0)
    net_debt_m = st.number_input('Net debt incl. leases (£m)', value=2410.0)
    st.caption('Verify price date, shares, debt and lease treatment against disclosures.')

st.subheader('1 · Five-year operating forecast')
c1,c2,c3,c4 = st.columns(4)
with c1: revenue0 = st.number_input('Base-year revenue (£m)', min_value=0.0, value=17273.6)
with c2: growth = st.number_input('Annual revenue growth (%)', value=4.5, step=0.5)/100
with c3: ebit_margin = st.number_input('EBIT margin (%)', value=6.0, step=0.5)/100
with c4: tax = st.number_input('Effective tax rate (%)', min_value=0.0, max_value=99.0, value=25.0)/100
c5,c6,c7,c8 = st.columns(4)
with c5: da_pct = st.number_input('D&A / revenue (%)', min_value=0.0, value=3.0)/100
with c6: capex_pct = st.number_input('CapEx / revenue (%)', min_value=0.0, value=4.0)/100
with c7: nwc_pct = st.number_input('Change in NWC / revenue (%)', value=0.5)/100
with c8: invested0 = st.number_input('Opening invested capital (£m)', min_value=0.01, value=6000.0)

rows=[]
rev=revenue0
capital=invested0
for year in range(1,6):
    rev *= 1+growth
    ebit=rev*ebit_margin
    nopat=ebit*(1-tax)
    da=rev*da_pct
    capex=rev*capex_pct
    dnwc=rev*nwc_pct
    fcff=nopat+da-capex-dnwc
    rows.append({'Year':f'FY+{year}', 'Revenue (£m)':rev, 'EBIT (£m)':ebit,
                 'NOPAT (£m)':nopat, 'D&A (£m)':da, 'CapEx (£m)':capex,
                 'ΔNWC (£m)':dnwc, 'FCFF (£m)':fcff, 'Opening invested capital (£m)':capital,
                 'ROIC (%)':100*nopat/capital if capital>0 else None})
    capital += capex-da+dnwc
forecast=pd.DataFrame(rows)
st.dataframe(forecast.style.format({col:'{:,.1f}' for col in forecast.columns if col not in ('Year','ROIC (%)')} | {'ROIC (%)':'{:.1f}%'}), use_container_width=True, hide_index=True)
st.download_button('Download forecast CSV',forecast.to_csv(index=False).encode(), 'marketlens_forecast.csv','text/csv')

st.subheader('2 · CAPM and WACC')
a,b,c,d=st.columns(4)
with a: rf=st.number_input('Risk-free rate (%)', value=4.0)/100
with b: beta=st.number_input('Levered beta', min_value=0.0, value=1.0, step=0.1)
with c: erp=st.number_input('Equity risk premium (%)', value=5.5)/100
with d: kd=st.number_input('Pre-tax cost of debt (%)', min_value=0.0, value=5.0)/100
ke=rf+beta*erp
mcap=price_p/100*shares_m
# Net debt is not the same as gross debt. Capital weights require an explicit gross debt input.
gross_debt=st.number_input('Gross interest-bearing debt incl. leases for WACC weights (£m)',min_value=0.0,value=2750.0)
weight_d=gross_debt/(mcap+gross_debt)
wacc=(1-weight_d)*ke+weight_d*kd*(1-tax)
cc1,cc2,cc3=st.columns(3)
cc1.metric('CAPM cost of equity',f'{ke:.2%}')
cc2.metric('WACC',f'{wacc:.2%}')
cc3.metric('Equity market value',f'£{mcap:,.0f}m')
st.caption('WACC uses gross debt for capital weights; equity bridge below uses net debt. Verify debt and lease definitions to avoid double counting.')

st.subheader('3 · Discounted cash flow (FCFF)')
terminal_g=st.number_input('Perpetual terminal growth (%)', value=2.0, step=0.25)/100
if wacc <= terminal_g:
    st.error('WACC must exceed perpetual growth for a valid Gordon-growth terminal value.')
else:
    fcffs=forecast['FCFF (£m)'].tolist()
    pv_fcff=sum(cf/(1+wacc)**i for i,cf in enumerate(fcffs,1))
    tv=fcffs[-1]*(1+terminal_g)/(wacc-terminal_g)
    pv_tv=tv/(1+wacc)**5
    ev=pv_fcff+pv_tv
    equity=ev-net_debt_m
    implied_p=100*equity/shares_m
    d1,d2,d3,d4=st.columns(4)
    d1.metric('DCF enterprise value',f'£{ev:,.0f}m')
    d2.metric('DCF equity value',f'£{equity:,.0f}m')
    d3.metric('DCF implied price',f'{implied_p:,.1f}p')
    d4.metric('Upside / downside',f'{implied_p/price_p-1:+.1%}')
    st.caption(f'Terminal value accounts for {pv_tv/ev:.1%} of EV' if ev>0 else 'DCF EV is non-positive')
    st.markdown('**DCF sensitivity: implied share price (p)**')
    rates=[wacc-0.01,wacc-0.005,wacc,wacc+0.005,wacc+0.01]
    gs=[terminal_g-0.01,terminal_g-0.005,terminal_g,terminal_g+0.005,terminal_g+0.01]
    sensitivity=[]
    for r in rates:
        line={'WACC':f'{r:.2%}'}
        for g in gs:
            label=f'{g:.2%}'
            if r<=g or r<=-1:
                line[label]=None
            else:
                pvs=sum(cf/(1+r)**i for i,cf in enumerate(fcffs,1))
                pvt=(fcffs[-1]*(1+g)/(r-g))/(1+r)**5
                line[label]=100*(pvs+pvt-net_debt_m)/shares_m
        sensitivity.append(line)
    st.dataframe(pd.DataFrame(sensitivity).set_index('WACC').style.format('{:,.1f}',na_rep='N/A'),use_container_width=True)

st.subheader('4 · Economic Returns / Economic Profit model')
st.caption('Economic profit = NOPAT − WACC × opening invested capital. This is an illustrative enterprise-value model; terminal capital and profit must be reconciled to the DCF forecast.')
econ=forecast[['Year','NOPAT (£m)','Opening invested capital (£m)','ROIC (%)']].copy()
econ['Capital charge (£m)']=econ['Opening invested capital (£m)']*wacc
econ['Economic profit (£m)']=econ['NOPAT (£m)']-econ['Capital charge (£m)']
st.dataframe(econ.style.format({col:'{:,.1f}' for col in econ.columns if col!='Year'}),use_container_width=True,hide_index=True)
if wacc>terminal_g:
    ep=econ['Economic profit (£m)'].tolist()
    pv_ep=sum(v/(1+wacc)**i for i,v in enumerate(ep,1))
    terminal_ep=ep[-1]*(1+terminal_g)/(wacc-terminal_g)
    ep_ev=invested0+pv_ep+terminal_ep/(1+wacc)**5
    ep_equity=ep_ev-net_debt_m
    x,y,z=st.columns(3)
    x.metric('Economic-profit EV',f'£{ep_ev:,.0f}m')
    y.metric('Economic-profit equity value',f'£{ep_equity:,.0f}m')
    z.metric('Implied price',f'{100*ep_equity/shares_m:,.1f}p')
    st.warning('Economic-profit terminal growth and capital reinvestment assumptions may not match the FCFF terminal model. Do not treat agreement between these models as guaranteed.')

st.subheader('5 · Disclosure & modelling controls')
st.info('Illustrative research calculator, not investment advice. Seed inputs are unverified and not live. Use only public information. Document source dates, accounting adjustments, lease treatment, minority interests and valuation assumptions before publication.')
