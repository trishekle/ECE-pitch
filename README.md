# Financial Anomaly Detection

A research prototype comparing three ways for language models to explain financial anomalies. All three prototypes use the same market/financial data retrieval and deterministic anomaly detector; only the explanation architecture changes.

> **Research question:** Does added reasoning complexity improve financial analysis enough to justify its extra latency and cost?

The project does not treat an anomaly as evidence of fraud or misconduct. Its purpose is to compare approaches, surface evidence and uncertainty, and document where the available data is insufficient.

## Prototypes

| Prototype | Approach | LLM calls |
| --- | --- | ---: |
| **P1 — Baseline** | A single LLM explains the detected anomalies and supplied financial data. | 1 |
| **P2 — Evidence-grounded** | Retrieves relevant SEC EDGAR Company Facts, then asks one LLM to explain the anomalies with that evidence. | 1 |
| **P3 — Multi-agent** | Financial, filing, and market agents analyze the case; a critic cross-checks their conclusions and prepares the final report. | 4 |

P2 is the interactive demo. The repository and evaluation cover all three prototypes.

## Shared analysis pipeline

```text
Ticker
  -> Yahoo Finance data retrieval
  -> Shared deterministic anomaly detection
  -> P1: baseline | P2: SEC evidence + LLM | P3: specialist agents + critic
  -> Explanation and evaluation
```

The detector currently checks:

- Revenue growth
- Operating-margin change
- Net-income versus operating-cash-flow divergence
- Debt change
- Financial performance versus market-price divergence

Thresholds are defined in [`src/detection/anomalies.py`](src/detection/anomalies.py). Yahoo Finance data is retrieved with `yfinance`; P2 and the filing agent use SEC EDGAR Company Facts. Public data availability, reporting periods, and provider coverage can differ, so results should be checked against the underlying filings.

## Try the interactive demo in Google Colab

[![Open in Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trishekle/ECE-pitch/blob/main/notebooks/financial_anomaly_demo.ipynb)

The notebook provides a small GUI for **Prototype 2 only**:

1. Open the notebook in Colab and run its cells in order.
2. Enter a ticker and its SEC CIK.
3. Click **Run Prototype 2**.

Live LLM inference requires an `AI_API_KEY` secret in Colab's Secrets panel. Without a key, the notebook can display a saved P2 result for a ticker found in [`outputs1.json`](outputs1.json). If no saved result is available, add the key to run a new analysis. Provider failures are shown as failures; they are not replaced with fabricated results.

## Run locally

Use Python 3.x and install the dependencies:

```bash
python -m venv .venv
```

Activate the virtual environment, then install the requirements:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

python -m pip install -r requirements.txt
```

Set `AI_API_KEY` in your shell or in a local `.env` file in the project root. The `.env` file is ignored by Git; **never commit API keys**.

```dotenv
AI_API_KEY=your_key_here
```

Run a prototype directly:

```bash
python -m src.prototypes.p1_baseline
python -m src.prototypes.p2_retrieval
python -m src.prototypes.p3_multiagent
```

These module entry points use the example AAPL case. The functions `run_p1`, `run_p2`, and `run_p3` can also be imported and called with another ticker (and, for P2/P3, a SEC CIK).

## Evaluation

The evaluation runner reads cases from [`cases.json`](cases.json), saves model outputs and measured latency to [`outputs1.json`](outputs1.json), and supports interactive human scoring in [`evaluation_results.json`](evaluation_results.json).

```bash
# Run all prototypes for cases that do not already have saved outputs
python -m src.evaluation.scorecard run

# Run just P1 and P2, or just P3
python -m src.evaluation.scorecard run-p1p2
python -m src.evaluation.scorecard run-p3

# Score unscored saved outputs, then print the scorecard
python -m src.evaluation.scorecard score
python -m src.evaluation.scorecard scorecard

# Run the detector's built-in threshold scenarios
python -m src.evaluation.test_detector
```

Evaluation calls may access external data services and a language-model API. They can take time, incur provider costs, or fail due to rate limits and service availability. Outputs are saved incrementally; failed runs should be recorded as failures, not treated as scores. The scorecard randomizes output order with a fixed seed to reduce prototype-identification bias, although writing style may still reveal which system produced an answer.

The explanation scorecard rates:

| Criterion | Scale |
| --- | ---: |
| Anomaly correctness | 0–1 |
| Evidence grounding | 0–2 |
| Explanation quality | 0–2 |
| Limitations and uncertainty | 0–2 |
| Unsupported claims | Count; lower is better |

The quality subtotal is grounding + explanation quality + limitations, with a maximum of 6. Latency is recorded as end-to-end wall-clock time for each run; the current examples are single-run measurements, not repeated-trial averages.

## Preliminary results

The currently recorded AAPL example illustrates trade-offs, but is too small to establish a winner:

| Prototype | Anomaly correct | Grounding | Explanation quality | Limitations | Unsupported claims | Quality subtotal / 6 | Latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P1 | 1 | 1 | 1 | 2 | 0 | 4 | 25.94 s |
| P2 | 1 | 2 | 1 | 2 | 1 | 5 | 31.52 s |
| P3 | 1 | 2 | 2 | 2 | 3 | 6 | 123.47 s |

P3 had the highest subtotal in this example, but also more unsupported claims and substantially longer latency. This is one human-scored case per prototype, not statistically significant evidence that one architecture is generally better.

A second recorded case, Coca-Cola (KO), has P1 and P2 outputs and was also scored. Both detected a medium market/financial divergence (revenue growth of about 1.87% versus stock return of about 34.1%). The saved P1 and P2 latencies were 56.74 s and 158.67 s, respectively. P3 did not complete for KO because of repeated Gemini HTTP 503 errors, so there is no P3 result for that case. The checked-in score file currently contains numeric ratings for the AAPL case only; KO ratings should not be inferred from its outputs.

See [`SLIDE_UPDATE.md`](SLIDE_UPDATE.md) for a presentation-oriented discussion of the examples, scoring, latency, and limitations.

## Limitations and responsible use

- A detector flag is a screening signal, not a causal explanation or an accusation.
- LLM explanations may include unsupported hypotheses; retrieved evidence does not guarantee every claim is grounded.
- Financial periods, market-return windows, and provider data may not align exactly.
- Missing or conflicting data can limit analysis; the system should state those limits rather than fill gaps with assumptions.
- Results depend on external data/API availability and model behavior.
- The current scorecard is a small pilot. A stronger comparison needs more varied cases, repeated latency runs, consistent inputs, blinded scoring, and preserved failures.

This prototype is for research and demonstration, not investment advice or automated financial decision-making.

## Repository layout

```text
src/
  data/          Yahoo Finance and SEC data retrieval
  detection/     Shared deterministic anomaly rules
  prototypes/    P1, P2, P3, and Gemini helper
  evaluation/    Detector scenarios and prototype scorecard
tests/           Example evaluation case definitions
notebooks/       P2-only interactive Colab demo
cases.json       Cases consumed by the evaluation runner
outputs1.json    Saved prototype outputs and run latencies
evaluation_results.json
                Human scorecard ratings
proto1.md        Example P1 analysis
proto2.md        Example P2 analysis
proto3.md        Example P3 analysis
```

## Data and API keys

The project uses publicly available market and SEC filing data. Live explanations use the Google GenAI SDK and require an API key provided locally through `AI_API_KEY` or through Colab Secrets. No key is included in the notebook or source code. Keep `.env` files private and do not publish credentials in outputs or screenshots.
