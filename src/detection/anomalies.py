import pandas as pd


ANOMALY_THRESHOLDS = {
    "revenue_growth": 0.20,        # 20%
    "margin_change": 0.05,         # 5 percentage points
    "cashflow_divergence": 0.20,   # 20%
    "debt_change": 0.20,           # 20%
    "market_financial_gap": 0.30,  # 30 percentage points
}


def _latest_two(df: pd.DataFrame, row_name: str):
    """Return previous and latest available values for a financial metric."""

    if row_name not in df.index:
        return None, None

    values = pd.to_numeric(df.loc[row_name], errors="coerce").dropna()

    if len(values) < 2:
        return None, None

    # Sort periods chronologically.
    try:
        values = values.sort_index()
    except Exception:
        pass

    return float(values.iloc[-2]), float(values.iloc[-1])


def _severity(change: float, threshold: float) -> str:
    """Convert anomaly magnitude into a simple severity level."""

    magnitude = abs(change)

    if magnitude >= threshold * 2:
        return "high"

    return "medium"


def detect_revenue_anomaly(income_statement: pd.DataFrame):
    previous, current = _latest_two(
        income_statement,
        "Total Revenue"
    )

    if previous is None or previous == 0:
        return None

    growth = (current - previous) / abs(previous)

    if abs(growth) < ANOMALY_THRESHOLDS["revenue_growth"]:
        return None

    return {
        "type": "revenue_change",
        "severity": _severity(
            growth,
            ANOMALY_THRESHOLDS["revenue_growth"]
        ),
        "metric": "revenue",
        "previous": previous,
        "current": current,
        "change": growth,
        "rule": "Revenue changed by more than configured threshold.",
    }


def detect_margin_anomaly(income_statement: pd.DataFrame):
    previous_revenue, current_revenue = _latest_two(
        income_statement,
        "Total Revenue"
    )

    previous_operating, current_operating = _latest_two(
        income_statement,
        "Operating Income"
    )

    if (
        previous_revenue is None
        or current_revenue is None
        or previous_operating is None
        or current_operating is None
        or previous_revenue == 0
        or current_revenue == 0
    ):
        return None

    previous_margin = previous_operating / previous_revenue
    current_margin = current_operating / current_revenue

    margin_change = current_margin - previous_margin

    if abs(margin_change) < ANOMALY_THRESHOLDS["margin_change"]:
        return None

    return {
        "type": "margin_change",
        "severity": _severity(
            margin_change,
            ANOMALY_THRESHOLDS["margin_change"]
        ),
        "metric": "operating_margin",
        "previous": previous_margin,
        "current": current_margin,
        "change": margin_change,
        "rule": "Operating margin changed by more than configured threshold.",
    }


def detect_cashflow_anomaly(
    income_statement: pd.DataFrame,
    cash_flow: pd.DataFrame
):
    previous_income, current_income = _latest_two(
        income_statement,
        "Net Income"
    )

    # yfinance commonly exposes this as
    # "Operating Cash Flow", but the exact label can vary.
    cashflow_row = None

    for candidate in [
        "Operating Cash Flow",
        "Total Cash From Operating Activities",
        "Cash Flow From Continuing Operating Activities",
    ]:
        if candidate in cash_flow.index:
            cashflow_row = candidate
            break

    if cashflow_row is None:
        return None

    previous_cashflow, current_cashflow = _latest_two(
        cash_flow,
        cashflow_row
    )

    if (
        previous_income is None
        or current_income is None
        or previous_cashflow is None
        or current_cashflow is None
        or previous_income == 0
        or previous_cashflow == 0
    ):
        return None

    income_change = (
        current_income - previous_income
    ) / abs(previous_income)

    cashflow_change = (
        current_cashflow - previous_cashflow
    ) / abs(previous_cashflow)

    # We are particularly interested when the two move
    # strongly in opposite directions.
    divergence = abs(income_change - cashflow_change)

    if divergence < ANOMALY_THRESHOLDS["cashflow_divergence"]:
        return None

    if income_change * cashflow_change >= 0:
        return None

    return {
        "type": "cashflow_divergence",
        "severity": _severity(
            divergence,
            ANOMALY_THRESHOLDS["cashflow_divergence"]
        ),
        "metric": "net_income_vs_operating_cashflow",
        "net_income_change": income_change,
        "operating_cashflow_change": cashflow_change,
        "change": divergence,
        "rule": (
            "Net income and operating cash flow moved "
            "in substantially different directions."
        ),
    }


def detect_debt_anomaly(balance_sheet: pd.DataFrame):
    debt_row = None

    for candidate in [
        "Total Debt",
        "Total Debt And Capital Lease Obligation",
        "Long Term Debt And Capital Lease Obligation",
    ]:
        if candidate in balance_sheet.index:
            debt_row = candidate
            break

    if debt_row is None:
        return None

    previous, current = _latest_two(
        balance_sheet,
        debt_row
    )

    if previous is None or previous == 0:
        return None

    change = (current - previous) / abs(previous)

    if abs(change) < ANOMALY_THRESHOLDS["debt_change"]:
        return None

    return {
        "type": "debt_change",
        "severity": _severity(
            change,
            ANOMALY_THRESHOLDS["debt_change"]
        ),
        "metric": "total_debt",
        "previous": previous,
        "current": current,
        "change": change,
        "rule": "Total debt changed by more than configured threshold.",
    }


def detect_market_divergence(
    income_statement: pd.DataFrame,
    market_history: pd.DataFrame
):
    previous_revenue, current_revenue = _latest_two(
        income_statement,
        "Total Revenue"
    )

    if (
        previous_revenue is None
        or previous_revenue == 0
        or market_history is None
        or market_history.empty
    ):
        return None

    revenue_growth = (
        current_revenue - previous_revenue
    ) / abs(previous_revenue)

    if "Close" not in market_history.columns:
        return None

    prices = market_history["Close"].dropna()

    if len(prices) < 2:
        return None

    # Approximate one-year market return using ~252 trading days.
    lookback = min(252, len(prices) - 1)

    old_price = float(prices.iloc[-lookback - 1])
    latest_price = float(prices.iloc[-1])

    if old_price == 0:
        return None

    market_return = (
        latest_price - old_price
    ) / abs(old_price)

    gap = abs(revenue_growth - market_return)

    if gap < ANOMALY_THRESHOLDS["market_financial_gap"]:
        return None

    return {
        "type": "market_financial_divergence",
        "severity": _severity(
            gap,
            ANOMALY_THRESHOLDS["market_financial_gap"]
        ),
        "metric": "revenue_growth_vs_stock_return",
        "revenue_growth": revenue_growth,
        "market_return": market_return,
        "change": gap,
        "rule": (
            "Revenue growth and stock-price performance "
            "showed a large divergence."
        ),
    }


def detect_anomalies(
    ticker: str,
    financials: dict,
    market_history: pd.DataFrame
):
    """
    Run all deterministic anomaly rules.

    This function does NOT claim fraud, manipulation,
    misconduct, or financial wrongdoing.
    """

    income_statement = financials["income_statement"]
    balance_sheet = financials["balance_sheet"]
    cash_flow = financials["cash_flow"]

    anomalies = []

    detectors = [
        detect_revenue_anomaly(income_statement),
        detect_margin_anomaly(income_statement),
        detect_cashflow_anomaly(
            income_statement,
            cash_flow
        ),
        detect_debt_anomaly(balance_sheet),
        detect_market_divergence(
            income_statement,
            market_history
        ),
    ]

    for result in detectors:
        if result is not None:
            anomalies.append(result)

    return {
        "ticker": ticker,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
    }


if __name__ == "__main__":
    from src.data.financials import get_financials
    from src.data.market import get_market_data

    ticker = "AAPL"

    financials = get_financials(ticker)
    market_data = get_market_data(ticker)

    result = detect_anomalies(
        ticker,
        financials,
        market_data["history"]
    )

    print("\nDetected anomalies:")
    for anomaly in result["anomalies"]:
        print(
            f"- {anomaly['type']} "
            f"({anomaly['severity']})"
        )
        print(f"  {anomaly}")