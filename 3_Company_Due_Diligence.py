"""MarketLens: standalone company due diligence and valuation workbench.
Place under pages/. Depends only on streamlit and pandas already in the project.
All example values are synthetic. No live financial or consensus feeds.
"""
import math
import json
from datetime import date
import pandas as pd
import streamlit as st

st.set_page_config(page_title='MarketLens | Company Due Diligence', layout='wide')
st.title('MarketLens | Company Due Diligence')
st.caption('Pre-publication research workbench · Company-agnostic · Manual inputs, transparent assumptions and evidence gates')
st.warning('All prefilled numbers are synthetic demonstration inputs, NOT actual financial data or recommendations. Replace them with verified, dated disclosures and estimates.')

# Helpers: amounts in millions of the selected currency, share count in millions.
def safe_div(a,b):
    return a/b if abs(b)>1e-10 else float('nan')
def fmt(v, suffix=''):
    return f'{v:,.2f}{suffix}' if math.isfinite(v) else 'N/A'
def pv_annuity(cashflows, rate):
    return sum(v/(1+rate)**i for i,v in enumerate(cashflows,1))
def implied_fcf_growth(ev, fcf0, wacc, terminal_g):
    """Solve constant 5-year FCFF growth given a fixed terminal g, if feasible."""
    def enterprise(g):
        f=[fcf0*(1+g)**i for i in range(1,6)]
        tv=f[-1]*(1+terminal_g)/(wacc-terminal_g)
        return pv_annuity(f,wacc)+tv/(1+wacc)**5
    low, high=-0.95,3.0
    if ev<enterprise(low) or ev>enterprise(high):
        return None
    for _ in range(100):
        mid=(low+high)/2
        if enterprise(mid)<ev: low=mid
        else: high=mid
    return (low+high)/2

def metric_table(df):
    st.dataframe(df, use_container_width=True, hide_index=True)

def num(label, value, key=None, min_value=None, max_value=None, step=1.0):
    kwargs={'value':float(value),'step':float(step)}
    if min_value is not None: kwargs['min_value']=float(min_value)
    if max_value is not None: kwargs['max_value']=float(max_value)
    if key is not None: kwargs['key']=key
    return st.number_input(label,**kwargs)

with st.sidebar:
    st.header('Research identity')
    company=st.text_input('Company','Example Company')
    ticker=st.text_input('Ticker','EXAMPLE').upper()
    currency=st.text_input('Currency','USD').upper()
    asof=st.date_input('Valuation / information cutoff',value=date.today())
    st.caption('Avoid mixing market prices, filings and consensus from incompatible dates.')
    st.header('Equity bridge')
    price=num('Price per share',100,min_value=0.01)
    shares=num('Diluted shares (millions)',1000,min_value=0.01)
    net_debt=num('Net debt incl. consistent lease treatment (millions)',5000)
    nonop=num('Non-operating assets / minority adjustments, net (millions)',0)
    dividend=num('Annual dividend per share',0,min_value=0)
    st.caption('Equity value = enterprise value − net debt + net non-operating assets. Adjust for minority interests and other claims consistently.')

marketcap=price*shares
enterprise_market=marketcap+net_debt-nonop
st.metric('Current equity market capitalisation',f'{marketcap/1000:,.2f} {currency} bn')

history_tab, quality_tab, industry_tab, forecast_tab, returns_tab, value_tab, expectations_tab, checklist_tab=st.tabs([
    '1 Historical financials','2 Quality & risks','3 TAM & competition','4 Five-year forecast',
    '5 ROIC & WACC','6 DCF & economic profit','7 Market expectations','8 Research gate'
])

with history_tab:
    st.subheader('Five-year financial statements (amounts in millions)')
    st.caption('Enter 5 comparable fiscal years oldest to newest. The example is synthetic. Upload a CSV with the same column names to populate historical values.')
    years=[f'FY-{i}' for i in range(4,0,-1)]+['FY0']
    base=pd.DataFrame({
        'Fiscal year':years,'Revenue':[30000.,39000.,50000.,65000.,85000.],
        'Gross profit':[15000.,21000.,28000.,39000.,53550.],
        'EBIT':[5000.,7800.,11500.,16500.,23800.],
        'Net income attributable':[3500.,5500.,8300.,12500.,18000.],
        'Operating cash flow':[4500.,7000.,11000.,16000.,22000.],
        'CapEx':[1500.,2000.,3000.,4000.,5000.],
        'D&A':[1000.,1200.,1500.,1900.,2400.],
        'Cash':[4000.,5000.,6000.,8000.,10000.],
        'Debt':[9000.,9500.,10000.,10500.,11000.],
        'Equity':[15000.,18000.,22000.,27000.,34000.],
        'Invested capital':[19000.,22000.,26000.,31000.,39000.],
        'Receivables':[2800.,3400.,4300.,5500.,7300.],
        'Inventory':[1500.,1900.,2600.,3300.,4500.],
        'Diluted shares (mn)':[1050.,1040.,1030.,1010.,1000.]
    })
    template=base.copy()
    st.download_button('Download historical data template',template.to_csv(index=False),'marketlens_historical_template.csv','text/csv')
    uploaded=st.file_uploader('Optional: upload historical CSV',type=['csv'],key='historical_upload')
    if uploaded:
        try:
            imported=pd.read_csv(uploaded)
            missing=set(base.columns)-set(imported.columns)
            if missing or len(imported)!=5:
                st.error(f'CSV must have exactly five rows and these missing columns: {sorted(missing)}')
            else: base=imported[base.columns]
        except Exception as e: st.error(f'Unable to read CSV: {e}')
    hist=st.data_editor(base,use_container_width=True,hide_index=True,num_rows='fixed',key='historical_editor')
    numeric_cols=[c for c in hist.columns if c!='Fiscal year']
    hist[numeric_cols]=hist[numeric_cols].apply(pd.to_numeric,errors='coerce')
    valid_hist=hist[numeric_cols].notna().all().all() and (hist['Revenue']>0).all() and (hist['Diluted shares (mn)']>0).all()
    if not valid_hist:
        st.error('Fill all numeric cells; revenue and diluted shares must be positive.');st.stop()
    latest=hist.iloc[-1]
    h=hist.copy()
    h['Revenue growth %']=h['Revenue'].pct_change()*100
    h['Gross margin %']=h['Gross profit']/h['Revenue']*100
    h['EBIT margin %']=h['EBIT']/h['Revenue']*100
    h['FCF']=h['Operating cash flow']-h['CapEx']
    h['FCF conversion %']=h['FCF']/h['Net income attributable'].replace(0,float('nan'))*100
    h['ROIC %']=(h['EBIT']*.79)/h['Invested capital'].rolling(2).mean()*100
    st.subheader('Historical diagnostics')
    st.dataframe(h[['Fiscal year','Revenue growth %','Gross margin %','EBIT margin %','FCF','FCF conversion %','ROIC %']].style.format(precision=1,na_rep='N/A'),use_container_width=True,hide_index=True)
    rev_cagr=(latest['Revenue']/hist.iloc[0]['Revenue'])**.25-1
    st.metric('Four-interval historical revenue CAGR',fmt(rev_cagr*100,'%'))
    st.caption('Illustrative ROIC in this historical summary uses a flat 21% tax assumption. The ROIC & WACC tab uses your selected tax rate.')

with quality_tab:
    st.subheader('Earnings quality, balance-sheet resilience and red flags')
    ocf=float(latest['Operating cash flow']); ni=float(latest['Net income attributable']); fcf=ocf-float(latest['CapEx'])
    quality=pd.DataFrame([
        {'Test':'Operating cash flow / attributable earnings','Value':fmt(safe_div(ocf,ni),'x'),'Interpretation':'Persistent low conversion warrants accrual and working-capital review'},
        {'Test':'Free cash flow / attributable earnings','Value':fmt(safe_div(fcf,ni),'x'),'Interpretation':'Inspect capex cycles, capitalised costs and one-offs'},
        {'Test':'Receivables growth vs revenue growth (last year)','Value':fmt((safe_div(float(latest['Receivables']),float(hist.iloc[-2]['Receivables']))-1)*100 - (safe_div(float(latest['Revenue']),float(hist.iloc[-2]['Revenue']))-1)*100,' pp'),'Interpretation':'Rising receivables faster than sales may indicate collection risk'},
        {'Test':'Inventory growth vs revenue growth (last year)','Value':fmt((safe_div(float(latest['Inventory']),float(hist.iloc[-2]['Inventory']))-1)*100 - (safe_div(float(latest['Revenue']),float(hist.iloc[-2]['Revenue']))-1)*100,' pp'),'Interpretation':'Check obsolescence, demand forecasting and supply build'},
        {'Test':'Debt / equity','Value':fmt(safe_div(float(latest['Debt']),float(latest['Equity'])),'x'),'Interpretation':'Compare with peers, cash, maturities and interest coverage'},
        {'Test':'Share count change (oldest to latest)','Value':fmt((safe_div(float(latest['Diluted shares (mn)']),float(hist.iloc[0]['Diluted shares (mn)']))-1)*100,'%'),'Interpretation':'Dilution or repurchases affect per-share value'},
    ])
    metric_table(quality)
    st.markdown('**Qualitative scrutiny (record evidence in Research gate)**')
    st.write('Accounting policies, non-GAAP adjustments, stock-based compensation, customer concentration, related parties, contingent liabilities, audit qualifications, debt covenants, governance, regulation, supply chain, cybersecurity, cyclicality, geographic exposure and management incentives.')

with industry_tab:
    st.subheader('Addressable market, demand and competitive economics')
    c1,c2,c3=st.columns(3)
    with c1:
        addressable=num('Current serviceable market (millions)',200000,min_value=0.01)
        relevant_share=num('Fraction of company revenue in this market (%)',80,min_value=0,max_value=100)
    with c2:
        tam_growth=num('Annual serviceable-market growth (%)',15,min_value=-50,max_value=100)
        market_share0=num('Estimated relevant market share (%)',25,min_value=0,max_value=100)
    with c3:
        addressable_capex=num('Customer addressable annual spending (millions)',180000,min_value=0)
        replacement=num('Replacement cycle (years)',4,min_value=1)
    relevant_revenue=float(latest['Revenue'])*relevant_share/100
    penetration=safe_div(relevant_revenue,addressable)
    st.metric('Revenue / estimated serviceable market',fmt(penetration*100,'%'))
    st.caption('Revenue/TAM is not necessarily installed-base penetration or market share. TAM definitions, product coverage and geography must match. Market share entered separately is an independent estimate.')
    tam_projection=pd.DataFrame({'Forecast year':[f'FY+{i}' for i in range(1,6)],'Estimated serviceable market (mn)':[addressable*(1+tam_growth/100)**i for i in range(1,6)]})
    metric_table(tam_projection.round(1))
    st.write('Validate TAM bottom-up: units × price × adoption × replacement frequency. Cross-check hyperscaler/customer capex, competitor capacity, substitution and price erosion. Total customer capex is not equal to spending available to this company.')
    st.caption(f'Illustrative customer addressable spend: {addressable_capex:,.0f} {currency} mn; assumed replacement cycle: {replacement:.1f} years; independently estimated market share: {market_share0:.1f}%.')

with forecast_tab:
    st.subheader('Integrated five-year operating and free-cash-flow forecast')
    st.caption('Revenue and margin drivers are editable by year. Forecast is based on the final historical year; amounts in millions.')
    c1,c2,c3=st.columns(3)
    with c1: tax=num('Effective operating tax rate (%)',21,min_value=0,max_value=60)
    with c2: initial_growth=num('Initial revenue growth assumption (%)',20,min_value=-90,max_value=200)
    with c3: initial_margin=num('Initial EBIT margin assumption (%)',28,min_value=-100,max_value=100)
    forecast_inputs=pd.DataFrame({
        'Year':[f'FY+{i}' for i in range(1,6)],
        'Revenue growth %':[initial_growth,initial_growth-3,initial_growth-6,initial_growth-9,initial_growth-12],
        'EBIT margin %':[initial_margin]*5,
        'D&A / revenue %':[3.]*5,
        'CapEx / revenue %':[6.]*5,
        'Change in NWC / revenue %':[1.]*5,
        'Net income / EBIT %':[70.]*5,
    })
    drivers=st.data_editor(forecast_inputs,hide_index=True,use_container_width=True,key='operating_drivers',disabled=['Year'])
    revenue=float(latest['Revenue']); forecast_rows=[]
    for _,r in drivers.iterrows():
        g=float(r['Revenue growth %'])/100
        if g<=-1: st.error('Revenue growth must exceed -100%.');st.stop()
        revenue*=1+g
        ebit=revenue*float(r['EBIT margin %'])/100
        nopat=ebit*(1-tax/100)
        da=revenue*float(r['D&A / revenue %'])/100
        capex=revenue*float(r['CapEx / revenue %'])/100
        delta_nwc=revenue*float(r['Change in NWC / revenue %'])/100
        fcff=nopat+da-capex-delta_nwc
        earnings=ebit*float(r['Net income / EBIT %'])/100
        forecast_rows.append({'Year':r['Year'],'Revenue':revenue,'EBIT':ebit,'NOPAT':nopat,'D&A':da,'CapEx':capex,'ΔNWC':delta_nwc,'FCFF':fcff,'Net income (simplified)':earnings,'EPS (constant shares)':earnings/shares})
    projection=pd.DataFrame(forecast_rows)
    st.dataframe(projection.style.format({c:'{:,.2f}' for c in projection.columns if c!='Year'}),hide_index=True,use_container_width=True)
    st.download_button('Download operating forecast',projection.to_csv(index=False),'marketlens_five_year_forecast.csv','text/csv')
    st.caption('Simplification: net income = EBIT × entered conversion; this is NOT a full three-statement forecast. EPS assumes constant diluted shares. Forecast ΔNWC is an annual incremental investment, not a balance-sheet level.')

with returns_tab:
    st.subheader('CAPM, WACC, ROIC and sustainable growth')
    a,b,c=st.columns(3)
    with a:
        rf=num('Risk-free rate (%)',4,min_value=-5,max_value=30)
        beta=num('Equity beta',1.3,min_value=0,max_value=5,step=.1)
        erp=num('Equity risk premium (%)',5,min_value=0,max_value=30)
    with b:
        cost_debt=num('Pre-tax cost of debt (%)',6,min_value=0,max_value=50)
        equity_weight=num('Target equity weight (%)',85,min_value=0,max_value=100)
        reinvestment=num('Reinvestment / NOPAT (%)',35,min_value=-100,max_value=200)
    with c:
        capital0=num('Starting invested capital (millions)',float(latest['Invested capital']),min_value=0.01)
        stable_roic=num('Terminal incremental ROIC (%)',18,min_value=-50,max_value=100)
    ke=(rf+beta*erp)/100
    wacc=(equity_weight/100)*ke+(1-equity_weight/100)*(cost_debt/100)*(1-tax/100)
    current_roic=float(latest['EBIT'])*(1-tax/100)/((float(hist.iloc[-2]['Invested capital'])+float(latest['Invested capital']))/2)
    st.metric('CAPM cost of equity',fmt(ke*100,'%'))
    st.metric('WACC',fmt(wacc*100,'%'))
    st.metric('Historical ROIC (average invested capital)',fmt(current_roic*100,'%'))
    st.metric('ROIC – WACC spread',fmt((current_roic-wacc)*100,' percentage points'))
    st.metric('Illustrative fundamental growth (ROIC × reinvestment)',fmt(current_roic*reinvestment,'%'))
    st.caption('Target capital weights, debt cost, risk-free tenor, beta estimation and country risk must be independently justified. Fundamental growth identity is approximate and assumes stable returns and reinvestment economics.')

with value_tab:
    st.subheader('DCF and residual economic-profit cross-check')
    a,b=st.columns(2)
    with a: terminal_g=num('Terminal FCFF growth (%)',3,min_value=-5,max_value=20,step=.5)
    with b: exit_roic=num('Incremental ROIC on reinvestment (%)',stable_roic,min_value=-50,max_value=100)
    if wacc<=terminal_g/100:
        st.error('WACC must exceed terminal growth for a Gordon-growth terminal value.');st.stop()
    fcff_list=projection['FCFF'].tolist()
    tv=fcff_list[-1]*(1+terminal_g/100)/(wacc-terminal_g/100)
    ev=pv_annuity(fcff_list,wacc)+tv/(1+wacc)**5
    equity=ev-net_debt+nonop
    per_share=equity/shares
    st.metric('DCF enterprise value (millions)',fmt(ev))
    st.metric('DCF implied equity value per share',fmt(per_share))
    st.metric('DCF upside / downside',fmt((safe_div(per_share,price)-1)*100,'%'))
    st.metric('Terminal value as % of enterprise value',fmt(safe_div(tv/(1+wacc)**5,ev)*100,'%'))
    sens=[]
    for wr in [-.02,-.01,0,.01,.02]:
        row={'WACC':f'{(wacc+wr)*100:.1f}%'}
        for gr in [-.02,-.01,0,.01,.02]:
            gg=terminal_g/100+gr
            if wacc+wr>gg and wacc+wr>-.99:
                vv=pv_annuity(fcff_list,wacc+wr)+fcff_list[-1]*(1+gg)/(wacc+wr-gg)/(1+wacc+wr)**5
                row[f'g={gg*100:.1f}%']=(vv-net_debt+nonop)/shares
            else: row[f'g={gg*100:.1f}%']=float('nan')
        sens.append(row)
    st.write('**DCF share-price sensitivity: WACC × terminal growth**')
    st.dataframe(pd.DataFrame(sens).style.format({k:'{:,.2f}' for k in sens[0] if k!='WACC'},na_rep='N/A'),hide_index=True,use_container_width=True)
    st.write('**Economic profit (residual operating income)**')
    capital=capital0; erows=[]
    for _,r in projection.iterrows():
        nopat=float(r['NOPAT']); ep=nopat-wacc*capital
        erows.append({'Year':r['Year'],'Opening invested capital':capital,'NOPAT':nopat,'Capital charge':wacc*capital,'Economic profit':ep})
        capital+=float(r['CapEx'])-float(r['D&A'])+float(r['ΔNWC'])
    ep_df=pd.DataFrame(erows)
    st.dataframe(ep_df.style.format({c:'{:,.2f}' for c in ep_df.columns if c!='Year'}),hide_index=True,use_container_width=True)
    # Consistent economic profit terminal based on the implied FCFF-based continuing enterprise value,
    # reconciled to end-of-forecast invested capital. This is an identity, not an independent valuation.
    ep_pv=pv_annuity(ep_df['Economic profit'].tolist(),wacc)
    terminal_operating_value=tv
    terminal_residual_value=terminal_operating_value-capital
    ep_ev=capital0+ep_pv+terminal_residual_value/(1+wacc)**5
    st.metric('Economic-profit enterprise value (millions)',fmt(ep_ev))
    st.caption('Economic-profit valuation uses starting invested capital, annual economic profits and terminal residual value. It should reconcile to DCF if starting invested capital and cash flows are internally consistent. Differences reveal inconsistencies in historical capital vs forecast net reinvestment; the terminal residual is derived from the DCF, not an independent terminal economic-profit forecast.')
    st.metric('DCF − economic-profit valuation difference (millions)',fmt(ev-ep_ev))

with expectations_tab:
    st.subheader('Forward multiples, reverse DCF, scenarios and return decomposition')
    eps0=safe_div(float(latest['Net income attributable']),float(latest['Diluted shares (mn)']))
    eps5=float(projection.iloc[-1]['EPS (constant shares)'])
    current_pe=safe_div(price,eps0)
    forward_pe=safe_div(price,eps5)
    st.metric('Trailing P/E from uploaded financials',fmt(current_pe,'x'))
    st.metric('P/E on FY+5 forecast EPS at unchanged share price',fmt(forward_pe,'x'))
    st.info('Forward P/E calculated at today’s price is not a prediction of the future P/E or share price.')
    if eps0>0 and eps5>0:
        eps_cagr=(eps5/eps0)**.2-1
        peg=safe_div(current_pe,eps_cagr*100)
        st.metric('Five-year EPS CAGR',fmt(eps_cagr*100,'%'))
        st.metric('PEG (trailing P/E / EPS CAGR in percentage points)',fmt(peg,'x'))
    else:
        st.warning('PEG and EPS CAGR not meaningful with nonpositive EPS.')
    cases=st.data_editor(pd.DataFrame({'Scenario':['Bear','Base','Bull'],'Year-5 EPS factor':[.70,1.,1.30], 'Year-5 exit P/E':[15.,25.,35.],'Probability %':[25.,50.,25.]}),hide_index=True,disabled=['Scenario'],key='scenario_editor',use_container_width=True)
    if (cases['Year-5 EPS factor']<=0).any() or (cases['Year-5 exit P/E']<=0).any() or (cases['Probability %']<0).any() or abs(cases['Probability %'].sum()-100)>0.01:
        st.error('Scenario factors and multiples must be positive; probabilities must sum to 100%.')
    else:
        cases['Implied year-5 price']=eps5*cases['Year-5 EPS factor']*cases['Year-5 exit P/E']
        cases['Five-year price return %']=(cases['Implied year-5 price']/price-1)*100
        cases['Annualised price return %']=((cases['Implied year-5 price']/price)**.2-1)*100
        metric_table(cases.round(2))
        weighted=(cases['Implied year-5 price']*cases['Probability %']/100).sum()
        st.metric('Probability-weighted year-5 price (not discounted)',fmt(weighted))
        st.metric('Annualised return on probability-weighted terminal price',fmt(((weighted/price)**.2-1)*100,'%'))
        st.caption('This is an illustrative scenario-weighted terminal price, not an expected annualised return or present value. Dividends and dilution excluded; probabilities are analyst assumptions.')
    st.write('**Market-implied five-year FCFF growth (reverse DCF)**')
    base_fcf=num('Starting normalised FCFF (millions)',max(float(projection.iloc[0]['FCFF']),1),min_value=.01)
    implied=implied_fcf_growth(enterprise_market,base_fcf,wacc,terminal_g/100)
    if implied is None: st.warning('No implied growth solution in the model range (-95% to +300% annual growth). Check FCFF, EV, WACC and terminal growth.')
    else: st.metric('Market-implied annual FCFF growth',fmt(implied*100,'%'))
    st.caption('Reverse DCF assumes one constant annual FCFF growth rate for five years and the entered perpetual terminal growth thereafter. It is highly sensitive to normalised starting FCFF, terminal value and capital structure.')
    consensus=num('Consensus FY+5 EPS (manual, if available)',0,min_value=0,step=.1)
    if consensus>0:
        st.metric('Your FY+5 EPS vs consensus',fmt((eps5/consensus-1)*100,'%'))
    else: st.info('Consensus not supplied. Leave zero until a dated, licensed/traceable estimate is available.')
    st.write('**P/E sensitivity: year-5 share price**')
    mults=[10.,15.,20.,25.,30.,40.]
    sensitivity=pd.DataFrame({'Exit P/E':mults,**{f'EPS {factor:.0%}':[eps5*factor*m for m in mults] for factor in [.7,.85,1.,1.15,1.3]}})
    metric_table(sensitivity.round(2))

with checklist_tab:
    st.subheader('Pre-publication evidence and scrutiny gate')
    st.caption('A model is not proof. Complete each research area with primary-source links, as-of dates and notes. The app will not certify an investment thesis.')
    checks=[
        ('Filings','Five annual reports and latest interim filing reconciled'),
        ('Accounting','Non-GAAP bridge, SBC, one-offs, taxes and cash conversion checked'),
        ('Balance sheet','Net debt, leases, debt maturities, liquidity and dilution checked'),
        ('Segment economics','Segment revenue, margins, product/customer mix verified'),
        ('Demand','TAM methodology and customer spending cross-checked'),
        ('Competition','Competitor margins, share, pricing and substitutes assessed'),
        ('ROIC','Invested capital and incremental ROIC reconciled'),
        ('Forecast','Growth, margins, reinvestment and FCFF supported by evidence'),
        ('Valuation','DCF, reverse DCF, terminal assumptions and multiples stress-tested'),
        ('Expectations','Consensus estimate date and key differences documented'),
        ('Risks','Governance, regulatory, geopolitics, concentration and catalysts reviewed'),
        ('Integrity','Public information only; conflicts, dates and uncertainties disclosed')]
    completed={}
    for key,description in checks:
        completed[key]=st.checkbox(f'{key}: {description}',key=f'gate_{key}')
    n=sum(completed.values())
    st.progress(n/len(checks),text=f'{n} of {len(checks)} review areas checked')
    if n<len(checks): st.warning(f'{len(checks)-n} scrutiny areas remain unchecked. Do not describe the research as complete.')
    else: st.success('All checklist items marked reviewed. Evidence quality and conclusions still require independent verification.')
    evidence=st.data_editor(pd.DataFrame({'Area':[x[0] for x in checks],'Source document / URL':['']*len(checks),'Publication / filing date':['']*len(checks),'Analyst finding / uncertainty':['']*len(checks)}),hide_index=True,use_container_width=True,key='evidence_editor')
    st.download_button('Export evidence log',evidence.to_csv(index=False),f'{ticker}_evidence_log.csv','text/csv')
    st.subheader('Research note')
    thesis=st.text_area('Investment thesis, variant perception, catalysts and falsification tests',height=180)
    notes={'company':company,'ticker':ticker,'currency':currency,'as_of':str(asof),'reviewed':completed,'analyst_note':thesis,'market_cap_mn':marketcap,'wacc':wacc,'dcf_value_per_share':per_share,'research_limitations':'Synthetic inputs until independently verified; manual estimates and evidence required.'}
    st.download_button('Export research summary (JSON)',json.dumps(notes,indent=2),'marketlens_research_summary.json','application/json')
    st.markdown('**Documents to collect**: annual/interim filings, earnings calls, segment disclosures, competitor filings, customer capex guidance, regulatory documents, shareholder structure, governance reports and dated consensus estimates.')
    st.caption('US filings: https://www.sec.gov/edgar/search/ | SEC XBRL API: https://www.sec.gov/search-filings/edgar-application-programming-interfaces | Other markets: use the relevant regulator and exchange.')
