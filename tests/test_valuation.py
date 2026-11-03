from src.valuation import market_cap, enterprise_value, pe_ratio, ev_multiple, dividend_yield

def test_market_cap():
    assert market_cap(400, 1000) == 4000

def test_ev():
    assert enterprise_value(4000, 500) == 4500

def test_pe():
    assert pe_ratio(4000, 400) == 10
    assert pe_ratio(4000, -20) is None

def test_ev_multiple():
    assert ev_multiple(4500, 500) == 9

def test_dividend_yield():
    assert dividend_yield(10, 400) == "2.50%"
