import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title='Levered Beta & CAPM | MarketLens', layout='wide')
st.title('Levered Beta, Bottom-Up Beta & CAPM')
st.caption('MarketLens research tool · Inputs are illustrative, not company data. Debt beta assumed zero in the simplified Hamada model.')

st.header('1. Capital structure and levered beta')
a,b,c = st.columns(3)
with a:
    beta_u = st.number_input('Unlevered beta', min_value=0.0, value=1.25, step=0.05)
    debt = st.number_input('Market value of interest-bearing debt (currency millions)', min_value=0.0, value=40000.0, step=1000.0)
with b:
    equity = st.number_input('Market value of equity (same currency millions)', min_value=0.01, value=200000.0, step=1000.0)
    tax = st.number_input('Marginal corporate tax rate (%)', min_value=0.0, max_value=100.0, value=25.0, step=0.5)/100
with c:
    rf = st.number_input('Risk-free rate (%)', value=4.0, step=0.25)/100
    erp = st.number_input('Equity risk premium (%)', min_value=0.0, value=5.0, step=0.25)/100
ratio = debt/equity
beta_l = beta_u*(1+(1-tax)*ratio)
ke = rf+beta_l*erp
m1,m2,m3,m4 = st.columns(4)
m1.metric('Debt / Equity', f'{ratio:.2%}')
m2.metric('Levered beta', f'{beta_l:.3f}')
m3.metric('CAPM cost of equity', f'{ke:.2%}')
m4.metric('Financial leverage multiplier', f'{1+(1-tax)*ratio:.3f}x')
st.latex(r'\beta_L = \beta_U\left[1+(1-T)\frac{D}{E}\right]')
st.latex(r'K_e = R_f + \beta_L\times ERP')
st.info('Use market values where available, a marginal tax rate, and a consistent definition of debt. The Hamada formula is an approximation; debt beta, tax shields and changing capital structures can matter.')

st.header('2. Bottom-up beta from comparable companies')
st.write('Enter peer equity betas and their debt/equity ratios. The median unlevered peer beta can be relevered to the target company.')
peers = pd.DataFrame({'Peer':['Peer A','Peer B','Peer C'], 'Levered beta':[1.60,1.40,1.80], 'Debt / equity (%)':[20.0,10.0,30.0], 'Marginal tax (%)':[25.0,25.0,25.0]})
peers = st.data_editor(peers, num_rows='dynamic', hide_index=True, use_container_width=True, key='beta_peers')
try:
    clean = peers.copy()
    for field in ['Levered beta','Debt / equity (%)','Marginal tax (%)']:
        clean[field] = pd.to_numeric(clean[field], errors='coerce')
    clean = clean.dropna(subset=['Levered beta','Debt / equity (%)','Marginal tax (%)'])
    clean = clean[(clean['Levered beta']>=0)&(clean['Debt / equity (%)']>=0)&clean['Marginal tax (%)'].between(0,100)]
    clean['Unlevered beta'] = clean['Levered beta']/(1+(1-clean['Marginal tax (%)']/100)*clean['Debt / equity (%)']/100)
    st.dataframe(clean, hide_index=True, use_container_width=True)
    if not clean.empty:
        median_u = float(clean['Unlevered beta'].median())
        bottom_up = median_u*(1+(1-tax)*ratio)
        bottom_up_ke = rf+bottom_up*erp
        x,y,z=st.columns(3)
        x.metric('Median peer unlevered beta',f'{median_u:.3f}')
        y.metric('Target relevered beta',f'{bottom_up:.3f}')
        z.metric('Bottom-up cost of equity',f'{bottom_up_ke:.2%}')
        st.download_button('Download peer beta calculations',clean.to_csv(index=False).encode(),file_name='marketlens_peer_beta.csv',mime='text/csv')
    else:
        st.warning('Add at least one valid peer.')
except Exception as exc:
    st.error(f'Please check the peer inputs: {exc}')

st.header('3. Historical regression beta')
st.write('Upload a CSV with **date**, **stock_price**, and **market_price** columns (adjusted prices preferred). Returns are calculated from consecutive rows. Use prices aligned to the same dates and currency where practical.')
upload = st.file_uploader('Historical prices CSV',type=['csv'],key='beta_price_csv')
if upload is not None:
    try:
        hist=pd.read_csv(upload)
        required={'date','stock_price','market_price'}
        if not required.issubset(hist.columns):
            st.error('Required columns: date, stock_price, market_price')
        else:
            hist['date']=pd.to_datetime(hist['date'],errors='coerce')
            for col in ['stock_price','market_price']:
                hist[col]=pd.to_numeric(hist[col],errors='coerce')
            hist=hist.dropna(subset=['date','stock_price','market_price']).sort_values('date').drop_duplicates('date')
            hist=hist[(hist.stock_price>0)&(hist.market_price>0)]
            returns=hist[['date']].copy()
            returns['Stock return']=hist.stock_price.pct_change()
            returns['Market return']=hist.market_price.pct_change()
            returns=returns.replace([np.inf,-np.inf],np.nan).dropna()
            if len(returns)<20 or returns['Market return'].var(ddof=1)<=0:
                st.warning('At least 20 valid return observations and nonzero market-return variance are needed.')
            else:
                reg_beta=returns['Stock return'].cov(returns['Market return'])/returns['Market return'].var(ddof=1)
                corr=returns['Stock return'].corr(returns['Market return'])
                r2=corr*corr
                q,w,e=st.columns(3)
                q.metric('Regression equity beta',f'{reg_beta:.3f}')
                w.metric('R-squared',f'{r2:.2%}')
                e.metric('Return observations',f'{len(returns)}')
                st.scatter_chart(returns,x='Market return',y='Stock return')
                st.download_button('Download aligned return observations',returns.to_csv(index=False).encode(),file_name='marketlens_beta_returns.csv',mime='text/csv')
    except Exception as exc:
        st.error(f'Unable to read CSV: {exc}')
else:
    st.code('date,stock_price,market_price\n2025-01-03,100,5000\n2025-01-10,103,5100\n2025-01-17,101,5070',language='csv')

st.header('4. Sensitivity: leverage and cost of equity')
levels=np.linspace(0,1.5,16)
sensitivity=pd.DataFrame({'Debt / Equity (%)':np.round(levels*100,1),'Levered beta':[beta_u*(1+(1-tax)*v) for v in levels]})
sensitivity['CAPM cost of equity (%)']=(rf+sensitivity['Levered beta']*erp)*100
st.line_chart(sensitivity.set_index('Debt / Equity (%)')[['Levered beta']])
st.dataframe(sensitivity.round(3),hide_index=True,use_container_width=True)
st.caption('Regression beta estimates historical equity sensitivity. Bottom-up beta uses peer operating risk adjusted for financial leverage. Neither is a guaranteed forecast of future volatility.')
