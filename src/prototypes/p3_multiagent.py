import os
import json
import hashlib
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from src.data.market import get_market_data
from src.data.financials import get_financials
from src.data.sec import get_relevant_facts
from src.detection.anomalies import detect_anomalies
from src.prototypes.gemini import generate_content_with_retry


load_dotenv()

MODEL = "gemini-3.5-flash"
CHECKPOINT_DIR = Path(__file__).resolve().parents[2] / ".p3_checkpoints"

client = genai.Client(
    api_key=os.getenv("AI_API_KEY")
)


def _load_checkpoint(ticker, cik):
    checkpoint_id = hashlib.sha256(f"{ticker}:{cik}".encode()).hexdigest()[:16]
    checkpoint_path = CHECKPOINT_DIR / f"{checkpoint_id}.json"
    if checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("ticker") != ticker or checkpoint.get("cik") != cik:
            raise ValueError(f"Checkpoint identity mismatch: {checkpoint_path}")
    else:
        checkpoint = {"ticker": ticker, "cik": cik, "agents": {}}
    return checkpoint, checkpoint_path


def _save_checkpoint(checkpoint, checkpoint_path):
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=CHECKPOINT_DIR,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(checkpoint, temp_file, indent=2)
            temp_file.write("\n")
        os.replace(temp_path, checkpoint_path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _generate_checkpointed(agent_id, prompt, checkpoint, checkpoint_path):
    signature = hashlib.sha256(f"{MODEL}\0{prompt}".encode()).hexdigest()
    saved = checkpoint["agents"].get(agent_id)
    if saved and saved["signature"] == signature:
        print(f"Resuming: reusing saved {agent_id} result.")
        return saved["response"]

    response = generate_content_with_retry(
        lambda: client.models.generate_content(model=MODEL, contents=prompt)
    )
    checkpoint["agents"][agent_id] = {
        "signature": signature,
        "response": response.text,
    }
    _save_checkpoint(checkpoint, checkpoint_path)
    return response.text


def call_agent(role, instructions, data, agent_id, checkpoint, checkpoint_path):
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

    return _generate_checkpointed(
        agent_id,
        prompt,
        checkpoint,
        checkpoint_path,
    )


def run_p3(ticker="AAPL", cik="320193"):

    print(f"\nRunning P3 Multi-Agent Analysis for {ticker}...")
    checkpoint, checkpoint_path = _load_checkpoint(ticker, cik)

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
        "financial_agent",
        checkpoint,
        checkpoint_path,
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
        "filing_agent",
        checkpoint,
        checkpoint_path,
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
        "market_agent",
        checkpoint,
        checkpoint_path,
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

    final_report = _generate_checkpointed(
        "critic_agent",
        critic_prompt,
        checkpoint,
        checkpoint_path,
    )

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