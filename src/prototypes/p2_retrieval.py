import json
import os

from dotenv import load_dotenv
from google import genai

from src.data.financials import get_financials
from src.data.market import get_market_data
from src.data.sec import get_relevant_facts
from src.detection.anomalies import detect_anomalies
from src.prototypes.gemini import generate_content_with_retry


load_dotenv()

client = genai.Client(
    api_key=os.getenv("AI_API_KEY")
)


def run_p2(ticker: str, cik: str):
    financials = get_financials(ticker)
    market_data = get_market_data(ticker)

    anomaly_result = detect_anomalies(
        ticker=ticker,
        financials=financials,
        market_history=market_data["history"],
    )

    sec_facts = get_relevant_facts(cik)

    prompt = f"""
You are a financial analysis assistant.

Analyze the detected financial anomalies using the supplied SEC evidence.

Ticker: {ticker}

Detected anomalies:
{json.dumps(anomaly_result, indent=2, default=str)}

SEC evidence:
{json.dumps(sec_facts, indent=2, default=str)}

Instructions:

1. Explain each detected anomaly.
2. Use the SEC evidence when relevant.
3. Clearly distinguish observed facts from possible explanations.
4. Do not claim fraud, manipulation, misconduct, or illegal activity.
5. Do not invent information that is not present in the supplied data.
6. If the evidence is insufficient, explicitly say so.
7. Prefer evidence-supported explanations over speculation.

Return:

Summary
Anomalies
Supporting Evidence
Possible Explanations
Limitations
"""

    response = generate_content_with_retry(
        lambda: client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
        )
    )

    return {
        "ticker": ticker,
        "anomalies": anomaly_result,
        "sec_evidence": sec_facts,
        "explanation": response.text,
    }


if __name__ == "__main__":
    result = run_p2("AAPL", "320193")

    print("\n" + "=" * 60)
    print("PROTOTYPE 2 — EVIDENCE GROUNDED")
    print("=" * 60)

    print("\nDetected anomalies:")

    for anomaly in result["anomalies"]["anomalies"]:
        print(
            f"- {anomaly['type']} "
            f"[{anomaly['severity']}]"
        )

    print("\nSEC evidence retrieved:")

    for fact in result["sec_evidence"]:
        print(f"- {fact}")

    print("\nLLM explanation:")
    print(result["explanation"])