import yfinance as yf


def get_company_info(symbol):
    """Fetch provider metadata for a ticker symbol."""
    return yf.Ticker(symbol).info


def get_market_info(symbol):
    """Fetch provider market info for a ticker symbol."""
    return yf.Ticker(symbol).info


def get_historical_prices(symbol, start_date, end_date):
    """Fetch provider historical daily prices for a ticker symbol."""
    return yf.Ticker(symbol).history(start=start_date, end=end_date)
