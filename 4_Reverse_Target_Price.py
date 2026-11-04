import streamlit as st
import pandas as pd

st.set_page_config(page_title='Reverse Target Price | MarketLens', layout='wide')
st.title('Reverse Target-Price Calculator')
st.caption('MarketLens | Scenario analysis. Inputs are illustrative, not live market data.')

with st.sidebar:
    st.header('Valuation assumptions')
    ticker = st.text_input('Company / ticker', 'NVDA')
    target = st.number_input('Target share price (USD)', min_value=0.01, value=370.0, step=5.0)
    profit = st.number_input('Forecast net income (USD billions)', min_value=0.01, value=217.17, step=1.0)
    shares = st.number_input('Forecast diluted shares (billions)', min_value=0.01, value=18.21, step=0.01)
    pe = st.number_input('Assumed target P/E (x)', min_value=0.01, value=50.0, step=1.0)
    current = st.number_input('Reference share price (USD)', min_value=0.01, value=250.0, step=5.0)

eps = profit / shares
implied_pe = target / eps
required_profit = target * shares / pe
fair_price = eps * pe
market_cap = target * shares / 1000
upside = (target / current - 1) * 100

st.subheader(f'{ticker.upper()} — target-price reverse engineering')
a,b,c = st.columns(3)
a.metric('Implied P/E at target', f'{implied_pe:,.2f}x')
b.metric('Net income required at assumed P/E', f'${required_profit:,.2f}B')
c.metric('Forecast EPS', f'${eps:,.2f}')
d,e,f = st.columns(3)
d.metric('Target market capitalisation', f'${market_cap:,.2f}T')
e.metric('Price at assumed P/E', f'${fair_price:,.2f}')
f.metric('Target return vs reference', f'{upside:+,.1f}%')

if abs(fair_price-target)/target > 0.01:
    st.warning('Your target price and assumed P/E imply different valuations. The implied P/E is calculated from the target and EPS; the assumed P/E is an independent input.')
else:
    st.success('Your target price and assumed P/E are consistent within 1%.')

st.subheader('P/E sensitivity — implied share price')
pe_levels = sorted(set([10,15,20,25,30,40,50,round(pe,2)]))
chart = pd.DataFrame({'P/E multiple': [f'{p:g}x' for p in pe_levels], 'Implied share price ($)': [eps*p for p in pe_levels]})
st.bar_chart(chart.set_index('P/E multiple'))

st.subheader('Earnings × P/E valuation matrix')
earnings_levels = [profit*x for x in (0.6,0.8,1.0,1.2,1.4)]
multiple_levels = [pe*x for x in (0.6,0.8,1.0,1.2,1.4)]
matrix = pd.DataFrame({f'${p:,.1f}B profit': [(p/shares)*m for m in multiple_levels] for p in earnings_levels}, index=[f'{m:.1f}x P/E' for m in multiple_levels])
st.dataframe(matrix.style.format('${:,.2f}'), use_container_width=True)

st.subheader('Earnings growth versus P/E compression')
col1,col2,col3=st.columns(3)
with col1: initial_pe=st.number_input('Starting P/E (x)', min_value=0.01, value=40.0)
with col2: ending_pe=st.number_input('Ending P/E (x)', min_value=0.01, value=25.0)
with col3: earnings_growth=st.number_input('Earnings growth (%)', min_value=-99.0, value=50.0)
return_pct=((1+earnings_growth/100)*(ending_pe/initial_pe)-1)*100
breakeven_growth=(initial_pe/ending_pe-1)*100
col1,col2=st.columns(2)
col1.metric('Implied share-price change',f'{return_pct:+.2f}%')
col2.metric('Earnings growth needed to break even',f'{breakeven_growth:.2f}%')
st.caption('Assumes constant diluted share count and excludes dividends. Earnings growth and multiple change must refer to the same forecast period.')

st.subheader('Export analysis')
export = pd.DataFrame([{'ticker':ticker,'target_price_usd':target,'net_income_usd_bn':profit,'diluted_shares_bn':shares,'assumed_pe':pe,'reference_price_usd':current,'forecast_eps_usd':eps,'implied_pe':implied_pe,'required_net_income_usd_bn':required_profit,'price_at_assumed_pe_usd':fair_price,'target_market_cap_usd_trillion':market_cap,'target_return_pct':upside}])
st.download_button('Download inputs and outputs (CSV)', export.to_csv(index=False), file_name=f'{ticker.lower()}_reverse_target_price.csv', mime='text/csv')
st.info('Research control: validate net income, diluted shares, valuation date, share splits and peer multiple assumptions from primary disclosures before publishing.')
