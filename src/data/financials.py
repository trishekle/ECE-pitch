import yfinance as yf


def get_financials(ticker: str):
    stock = yf.Ticker(ticker)

    return {
        "income_statement": stock.income_stmt,
        "balance_sheet": stock.balance_sheet,
        "cash_flow": stock.cashflow,
    }


if __name__ == "__main__":
    data = get_financials("AAPL")

    print("Income statement:")
    print(data["income_statement"].head())

    print("\nBalance sheet:")
    print(data["balance_sheet"].head())

    print("\nCash flow:")
    print(data["cash_flow"].head())


    print(data["income_statement"].index.tolist())
    print(data["balance_sheet"].index.tolist())
    print(data["cash_flow"].index.tolist())