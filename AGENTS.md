# Project Instructions — Financial Anomaly Detection

## Project Goal

Build a functional prototype for evidence-grounded financial anomaly detection.

The project compares three architectures:

1. Prototype 1 — Baseline LLM
2. Prototype 2 — Evidence-grounded retrieval + LLM
3. Prototype 3 — Multi-agent cross-checking

The goal is to experimentally compare quality, reliability, cost, latency, and complexity.

Do NOT assume that Prototype 3 is better. The evaluation should determine which architecture performs best under the defined metrics.

---

## Core Research Question

> Does increasing AI system complexity improve the quality of financial anomaly analysis enough to justify its additional cost and latency?

---

## Architecture

All three prototypes MUST share the same:

* data ingestion layer
* normalized financial data
* anomaly detection rules
* evaluation dataset
* evaluation metrics

Only the reasoning/explanation architecture should differ.

```text
Ticker
  ↓
Data ingestion
  ↓
Normalization
  ↓
Deterministic anomaly detection
  ↓
┌──────────────┬──────────────────┬─────────────────────┐
│ Prototype 1  │ Prototype 2      │ Prototype 3         │
│ Single LLM   │ Retrieval + LLM  │ Multi-agent + critic │
└──────────────┴──────────────────┴─────────────────────┘
  ↓
Evaluation
```

---

## Technology

Primary language:

* Python 3.x

Initial libraries:

* pandas
* numpy
* yfinance
* requests
* python-dotenv
* openai
* streamlit
* jupyter

Potential later additions:

* LangChain / LangGraph if they provide a clear benefit
* a vector database only if retrieval requirements justify it

Do NOT add dependencies simply because they are common in AI projects.

---

## Data Sources

Use:

1. SEC EDGAR as the authoritative source for company filings and reported financial information.
2. yfinance for market data and convenient financial-data access.

Where possible, preserve source metadata and evidence references.

Do not fabricate financial data or sources.

---

## Deterministic Anomaly Detection

Financial anomaly detection should primarily be deterministic Python logic rather than LLM reasoning.

Initial anomaly categories:

1. Revenue changes
2. Profitability / margin changes
3. Earnings vs. operating cash-flow divergence
4. Debt / liquidity changes
5. Financial performance vs. market-price divergence

The anomaly detector should produce structured data.

Example:

```python
{
    "ticker": "AAPL",
    "period": "2025",
    "anomalies": [
        {
            "type": "margin_change",
            "metric": "operating_margin",
            "previous": 0.18,
            "current": 0.11,
            "change": -0.07,
            "severity": "high"
        }
    ]
}
```

LLMs should NOT be responsible for basic numerical calculations that can be performed deterministically.

---

## Prototype 1

Prototype 1 is the simplest baseline.

```text
Anomaly
  ↓
LLM
  ↓
Explanation
```

The LLM receives:

* detected anomaly
* relevant financial figures
* available evidence

The explanation must distinguish:

* observed facts
* evidence-supported interpretations
* possible explanations
* unsupported conclusions

---

## Prototype 2

Prototype 2 adds evidence retrieval.

```text
Anomaly
  ↓
Evidence retrieval
  ↓
Relevant filings / financial evidence
  ↓
LLM
  ↓
Explanation
```

Prototype 2 should test whether improved evidence/context produces better grounded explanations.

Do not change the underlying anomaly detection rules.

---

## Prototype 3

Prototype 3 introduces specialized agents and cross-checking.

Conceptually:

```text
                    Evidence
                       ↓
       ┌───────────────┼───────────────┐
       ↓               ↓               ↓
   Financial        Filing          Market
     Agent           Agent           Agent
       └───────────────┼───────────────┘
                       ↓
                  Critic Agent
                       ↓
                Final explanation
```

Agents should have distinct responsibilities.

Do NOT create multiple agents that perform essentially the same task.

The critic should explicitly check whether conclusions are supported by evidence.

A financial anomaly must NOT automatically be interpreted as fraud, manipulation, or wrongdoing.

---

## LLM Safety / Grounding Requirements

LLM outputs must:

* use supplied evidence
* avoid fabricated facts
* avoid fabricated sources
* distinguish facts from hypotheses
* explicitly state uncertainty
* avoid unsupported accusations
* state when evidence is insufficient

An anomaly is not evidence of fraud by itself.

The system should prefer:

> "The data shows X. One possible explanation is Y, but the available evidence is insufficient to establish this."

over:

> "The company manipulated its earnings."

---

## Evaluation

All three prototypes must run against the same test set.

Initial target:

20–30 test cases.

Test cases should include:

* obvious anomalies
* normal companies/periods
* ambiguous cases
* missing data
* conflicting evidence
* cases designed to trigger unsupported speculation

Evaluate:

* anomaly detection accuracy
* explanation correctness
* evidence grounding
* unsupported claims / hallucinations
* false positives
* latency
* API/LLM cost

Do not optimize the evaluation dataset around whichever prototype performs best.

---

## Fair Comparison

When comparing prototypes:

* Use the same input cases.
* Use the same anomaly detector.
* Use the same financial data where possible.
* Keep evaluation criteria identical.
* Record latency.
* Record number of LLM calls.
* Estimate API cost.
* Preserve failed examples.

The objective is an honest comparison, not proving that the most complex architecture wins.

---

## Development Strategy

Build incrementally.

Priority order:

1. Data retrieval
2. Data normalization
3. Deterministic anomaly detection
4. Prototype 1
5. Evaluation framework
6. Prototype 2
7. Prototype 3
8. Evaluation comparison
9. Streamlit/demo polish
10. Colab notebook
11. Presentation

Do not build the UI before the core pipeline works.

Do not build the multi-agent system before Prototype 1 works.

Do not add advanced infrastructure unless it solves a demonstrated problem.

---

## Project Structure

Preferred structure:

```text
financial-anomaly-detector/
│
├── src/
│   ├── data/
│   │   ├── market.py
│   │   ├── financials.py
│   │   └── sec.py
│   │
│   ├── detection/
│   │   └── anomalies.py
│   │
│   ├── prototypes/
│   │   ├── p1_baseline.py
│   │   ├── p2_retrieval.py
│   │   └── p3_multiagent.py
│   │
│   └── evaluation/
│       └── evaluate.py
│
├── tests/
│   └── test_cases.json
│
├── notebooks/
│   └── demo.ipynb
│
├── app.py
├── requirements.txt
├── .env
├── .gitignore
├── AGENTS.md
└── README.md
```

---

## Coding Standards

Prefer:

* small functions
* clear type hints
* structured return values
* explicit error handling
* reproducible experiments
* minimal dependencies
* readable code

Avoid:

* giant scripts
* duplicated logic between prototypes
* hardcoded financial values
* hidden API calls
* unnecessary abstractions
* unnecessary frameworks

Keep shared functionality in `src/` and make prototypes consume it.

---

## Secrets

Never commit API keys.

Use `.env` locally.

`.env` must be included in `.gitignore`.

Never print API keys in logs, notebooks, or output.

---

## Notebook Requirements

A Google Colab notebook will be provided as a reproducible demonstration.

The notebook should:

1. Install dependencies.
2. Load/configure the project.
3. Accept a ticker.
4. Retrieve data.
5. Detect anomalies.
6. Run the available prototypes.
7. Display explanations.
8. Run/evaluate test cases.
9. Display comparison results.

Avoid putting the entire project implementation directly into notebook cells.

The notebook should demonstrate the project, not replace its source code.

---

## Resource Constraints

The project is intentionally time-constrained.

Prefer simple solutions that can be implemented and evaluated quickly.

GPU is NOT required unless a local model is deliberately introduced.

API-based LLM inference is acceptable.

Do not introduce a local LLM, vector database, distributed system, or complex infrastructure unless there is a clear experimental reason.

---

## Important Development Rule

When asked to implement a feature:

1. Check whether existing architecture already supports it.
2. Reuse shared components.
3. Avoid duplicating logic.
4. Keep Prototype 1, 2, and 3 experimentally comparable.
5. Prefer the smallest implementation that satisfies the requirement.

Do not automatically make the architecture more complex.

The purpose of this project is to **measure whether complexity helps**, not to maximize complexity.
