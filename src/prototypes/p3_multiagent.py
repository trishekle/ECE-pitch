import os
import json

from dotenv import load_dotenv
from google import genai

from src.data.market import get_market_data
from src.data.financials import get_financials
from src.data.sec import get_relevant_facts
from src.detection.anomalies import detect_anomalies
from src.prototypes.gemini import generate_content_with_retry


load_dotenv()

MODEL = "gemini-3.5-flash"

client = genai.Client(
    api_key=os.getenv("AI_API_KEY")
)


def call_agent(role, instructions, data):
    """Run one specialized financial-analysis agent."""

    prompt = f"""
You are the {role} in a financial anomaly detection system.

TASK:
{instructions}

SAFETY AND ACCURACY RULES:
- Only use facts contained in the supplied data.
- Clearly distinguish observations from possible explanations.
- Do not claim fraud, manipulation, misconduct, or illegal activity.
- Do not invent financial values, dates, events, or sources.
- If the evidence is insufficient, explicitly say so.
- Do not treat an anomaly as proof of wrongdoing.

SUPPLIED DATA:
{json.dumps(data, indent=2, default=str)}

Return these sections:

Key Observations
Relevant Evidence
Possible Explanations
Uncertainties
"""

    response = generate_content_with_retry(
        lambda: client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
    )

    return response.text


def run_p3(ticker="AAPL", cik="320193"):

    print(f"\nRunning P3 Multi-Agent Analysis for {ticker}...")

    # ---------------------------------------------------------
    # 1. Retrieve the same underlying data used by P1 and P2
    # ---------------------------------------------------------

    print("\nCollecting financial and market data...")

    financials = get_financials(ticker)
    market_data = get_market_data(ticker)

    # ---------------------------------------------------------
    # 2. Run deterministic anomaly detector
    # ---------------------------------------------------------

    anomalies = detect_anomalies(
        ticker,
        financials,
        market_data["history"]
    )

    print(
        f"Detected {anomalies['anomaly_count']} anomal"
        f"{'y' if anomalies['anomaly_count'] == 1 else 'ies'}."
    )

    # ---------------------------------------------------------
    # 3. Retrieve SEC evidence
    # ---------------------------------------------------------

    print("Retrieving SEC evidence...")

    sec_evidence = get_relevant_facts(cik)

    # ---------------------------------------------------------
    # 4. Financial Agent
    # ---------------------------------------------------------

    print("\n[1/4] Financial Agent...")

    financial_agent = call_agent(
        "Financial Agent",
        """
Analyze the company's financial statements and the detected
anomalies.

Focus on:
- revenue
- operating income
- operating margin
- net income
- operating cash flow
- debt

Identify important relationships between these metrics.
""",
        {
            "ticker": ticker,
            "anomalies": anomalies,
            "financials": financials,
        },
    )

    # ---------------------------------------------------------
    # 5. Filing Agent
    # ---------------------------------------------------------

    print("[2/4] Filing Agent...")

    filing_agent = call_agent(
        "SEC Filing Agent",
        """
Analyze the SEC-derived financial evidence.

Focus on:
- whether the detected anomaly is supported by filing data
- reported financial values
- fiscal periods
- consistency between the anomaly and SEC evidence

Do not infer information that is not present.
""",
        {
            "ticker": ticker,
            "anomalies": anomalies,
            "sec_evidence": sec_evidence,
        },
    )

    # ---------------------------------------------------------
    # 6. Market Agent
    # ---------------------------------------------------------

    print("[3/4] Market Agent...")

    market_agent = call_agent(
        "Market Agent",
        """
Analyze the relationship between financial performance and
market performance.

Focus on:
- revenue growth
- stock-price performance
- market/financial divergence
- whether the market evidence supports the detected anomaly

Only discuss relationships supported by the supplied data.
""",
        {
            "ticker": ticker,
            "anomalies": anomalies,
            "market_data": market_data,
        },
    )

    # ---------------------------------------------------------
    # 7. Critic Agent
    # ---------------------------------------------------------

    print("[4/4] Critic Agent...")

    critic_prompt = f"""
You are the Critic Agent in a financial anomaly detection system.

You received analyses from three specialized agents.

Your job is to:
1. Determine which observations are supported by evidence.
2. Identify contradictions between agents.
3. Remove unsupported claims.
4. Prefer concrete financial values over vague statements.
5. Produce one cautious final explanation.

IMPORTANT:
- Do NOT claim fraud, manipulation, misconduct, or illegal activity.
- Do NOT invent facts.
- Distinguish observed facts from possible explanations.
- If evidence is insufficient, say so.

DETECTED ANOMALIES:
{json.dumps(anomalies, indent=2, default=str)}

FINANCIAL AGENT:
{financial_agent}

SEC FILING AGENT:
{filing_agent}

MARKET AGENT:
{market_agent}

Return exactly these sections:

Summary
Anomalies
Evidence
Agent Agreement
Agent Disagreement
Possible Explanations
Limitations
"""

    response = generate_content_with_retry(
        lambda: client.models.generate_content(
            model=MODEL,
            contents=critic_prompt,
        )
    )

    final_report = response.text

    # ---------------------------------------------------------
    # 8. Display final result
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("P3 FINAL REPORT")
    print("=" * 70)

    print(final_report)

    return {
        "ticker": ticker,
        "anomalies": anomalies,
        "financial_agent": financial_agent,
        "filing_agent": filing_agent,
        "market_agent": market_agent,
        "final_report": final_report,
    }


if __name__ == "__main__":
    run_p3()