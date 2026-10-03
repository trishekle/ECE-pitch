import yfinance as yf


def get_market_data(ticker: str, period: str = "5y"):
    stock = yf.Ticker(ticker)

    history = stock.history(period=period)
    info = stock.info

    return {
        "history": history,
        "info": info,
    }