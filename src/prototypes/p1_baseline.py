import json
import os

from dotenv import load_dotenv
from google import genai

from src.data.financials import get_financials
from src.data.market import get_market_data
from src.detection.anomalies import detect_anomalies


load_dotenv()

client = genai.Client(
    api_key=os.getenv("AI_API_KEY")
)


def run_p1(ticker: str):
    # Get financial and market data
    financials = get_financials(ticker)
    market_data = get_market_data(ticker)

    # Detect anomalies deterministically
    anomaly_result = detect_anomalies(
        ticker=ticker,
        financials=financials,
        market_history=market_data["history"],
    )

    # The LLM explains the detected anomalies.
    # It does NOT determine whether fraud or manipulation occurred.
    prompt = f"""
You are a financial analysis assistant.

Analyze the following automatically detected financial anomalies.

Ticker: {ticker}

Detected anomalies:

{json.dumps(anomaly_result, indent=2, default=str)}

For each anomaly:

1. Explain what changed.
2. Explain why the change may matter financially.
3. Clearly distinguish observations from possible explanations.
4. Do not claim fraud, manipulation, misconduct, or illegal activity.
5. Do not invent facts that are not present in the supplied data.
6. If the available information is insufficient, say so.

Return your answer with these sections:

Summary
Anomalies
Possible Explanations
Limitations
"""

    # Gemini API call
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )

    return {
        "ticker": ticker,
        "anomalies": anomaly_result,
        "explanation": response.text,
    }


if __name__ == "__main__":
    result = run_p1("AAPL")

    print("\n" + "=" * 60)
    print("PROTOTYPE 1 — BASELINE")
    print("=" * 60)

    print("\nDetected anomalies:")

    for anomaly in result["anomalies"]["anomalies"]:
        print(
            f"- {anomaly['type']} "
            f"[{anomaly['severity']}]"
        )

    print("\nLLM explanation:")
    print(result["explanation"])