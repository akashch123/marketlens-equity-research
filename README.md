# MarketLens — Equity Valuation & Market Expectations

A GitHub-ready Streamlit MVP for independent equity research. Initial coverage: Marks and Spencer Group plc (MKS.L).

## Features
- Reported, management-adjusted and analyst-normalised P/E
- Market capitalisation and enterprise value
- EV/EBITDA and EV/EBIT
- Dividend yield
- Editable accounting adjustment bridge
- Peer-group P/E statistics
- Bear/base/bull scenario valuation
- CSV download of current inputs

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
1. Create a public GitHub repository named `marketlens-equity-research`.
2. Upload this project.
3. Sign in to Streamlit Community Cloud and connect the repository.
4. Set the main file path to `app.py`.
5. Deploy.

## Data conventions
- All financial statement inputs in the dashboard are GBP millions unless specified.
- Share price and dividend per share are entered in pence.
- Diluted shares are entered in millions.
- Market capitalisation (£m) = share price (£) × diluted shares (m).
- P/E = market capitalisation (£m) / earnings attributable to ordinary shareholders (£m).
- EV = market capitalisation + net debt. Define net debt consistently and state whether lease liabilities are included.
- The app does not infer attributable earnings from PBT. Enter reported/adjusted/normalised attributable earnings separately.
- Peer statistics use market capitalisation and earnings on a consistent currency, period and accounting basis.

## M&S seed data and cautions
The sample share price of 412p is taken from the user's Yahoo Finance screenshot dated 30 October 2026. The draft research note supplied by the user stated FY26 revenue of £17,273.6m and net debt including lease liabilities of £2,410m. These are seed values only and should be checked against the official FY26 annual report before publication. The earnings inputs intentionally default to zero because PBT is not equivalent to earnings attributable to ordinary shareholders.

The peer list is a starter universe, not a claim that all peers are directly comparable. Populate peer financials only after verifying the same reporting period, share-count basis, currency and earnings definition.

## Project safeguards
- This is an analytical/research tool, not personalised investment advice.
- It does not make automated buy/sell recommendations.
- Clearly disclose conflicts, holdings and relevant employment.
- Do not enter confidential employer information or use non-public information.
- Confirm API terms, exchange data rights and redistribution permissions before adding live market data.

## Next development steps
1. Add annual historical financial statements and a source/date field for every observation.
2. Build a normalisation policy with item-level tax and minority-interest treatment.
3. Add sector-specific peer sets and historical valuation bands.
4. Add a licensed market-data API adapter.
5. Add a valuation history database and audit trail.
