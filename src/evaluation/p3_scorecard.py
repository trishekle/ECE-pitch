# eval.py
import argparse
import json
import os
import random
import statistics as st
import tempfile
from pathlib import Path

from src.prototypes.p1_baseline import run_p1
from src.prototypes.p2_retrieval import run_p2
from src.prototypes.p3_multiagent import run_p3

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CASES_FILE = PROJECT_ROOT / "cases.json"
OUTPUTS_FILE = PROJECT_ROOT / "outputs.json"
SCORES_FILE = PROJECT_ROOT / "evaluation_results.json"

def _run_p1(ticker, cik):
    del cik
    return run_p1(ticker)

# ---- 1. Plug your prototypes in here ----
PROTOTYPES = {
    "P1": _run_p1,
    "P2": run_p2,
    "P3": run_p3,
}

def load_cases():
    if not CASES_FILE.is_file():
        raise SystemExit(
            f"Cases file not found: {CASES_FILE}. "
            'Create a JSON array with entries like '
            '{"case_id": "aapl", "input": {"ticker": "AAPL", "cik": "320193"}}.'
        )
    return json.loads(CASES_FILE.read_text(encoding="utf-8"))


def save_outputs(outputs):
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=OUTPUTS_FILE.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(outputs, temp_file, indent=2)
            temp_file.write("\n")
        os.replace(temp_path, OUTPUTS_FILE)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def run_prototypes(prototype_names):
    cases = load_cases()
    outputs = json.loads(OUTPUTS_FILE.read_text(encoding="utf-8")) if OUTPUTS_FILE.exists() else []
    completed = {(item["prototype"], item["case_id"]) for item in outputs}
    saved_count = 0

    for case in cases:
        for name in prototype_names:
            key = (name, case["case_id"])
            if key in completed:
                print(f"Already saved {name} for case {case['case_id']}; skipping.")
                continue

            result = PROTOTYPES[name](**case["input"])
            outputs.append({
                "prototype": name,
                "case_id": case["case_id"],
                "output": result,
            })
            save_outputs(outputs)
            completed.add(key)
            saved_count += 1
            print(f"Saved {name} output for case {case['case_id']}.")

    print(f"Saved {saved_count} new outputs to {OUTPUTS_FILE}.")


def cmd_run():
    run_prototypes(tuple(PROTOTYPES))


def cmd_run_p1p2():
    run_prototypes(("P1", "P2"))


def cmd_run_p3():
    run_prototypes(("P3",))

# ---- 2. Blind scoring ----
def ask(prompt, valid):
    while True:
        v = input(prompt).strip()
        if v.isdigit() and int(v) in valid:
            return int(v)

def cmd_score():
    outputs = json.loads(OUTPUTS_FILE.read_text())
    scores = json.loads(SCORES_FILE.read_text()) if SCORES_FILE.exists() else []
    done = {(s["prototype"], s["case_id"]) for s in scores}
    todo = [o for o in outputs if (o["prototype"], o["case_id"]) not in done]
    random.Random(0).shuffle(todo)   # hides which prototype produced what

    for i, o in enumerate(todo, 1):
        print(f"\n--- {i}/{len(todo)} | case {o['case_id']} ---\n{o['output']}\n")
        scores.append({
            "prototype": o["prototype"], "case_id": o["case_id"],
            "anomaly_correct": ask("anomaly_correct (0-1): ", {0, 1}),
            "grounding": ask("grounding (0-2): ", {0, 1, 2}),
            "explanation_quality": ask("quality (0-2): ", {0, 1, 2}),
            "limitations": ask("limitations (0-2): ", {0, 1, 2}),
            "unsupported_claims": ask("unsupported claims (count): ", set(range(50))),
        })
        SCORES_FILE.write_text(json.dumps(scores, indent=2))  # save after each

# ---- 3. Scorecard ----
def cmd_scorecard():
    scores = json.loads(SCORES_FILE.read_text())
    if not scores:
        print("No scores found. Run the evaluation, then score its outputs:")
        print("  python -m src.evaluation.p3_scorecard run")
        print("  python -m src.evaluation.p3_scorecard score")
        return

    print(f"\n{'Proto':<8}{'N':<4}{'Acc':<8}{'Ground':<9}{'Qual':<8}{'Limits':<9}{'Unsup/case':<12}{'Quality/6':<10}")
    print("-" * 67)
    for p in sorted({s["prototype"] for s in scores}):
        r = [s for s in scores if s["prototype"] == p]
        m = lambda k: st.mean(x[k] for x in r)
        q = m("grounding") + m("explanation_quality") + m("limitations")
        print(f"{p:<8}{len(r):<4}{m('anomaly_correct'):<8.2f}{m('grounding'):<9.2f}"
              f"{m('explanation_quality'):<8.2f}{m('limitations'):<9.2f}"
              f"{m('unsupported_claims'):<12.2f}{q:<10.2f}")

def main():
    parser = argparse.ArgumentParser(description="Run and score the prototype evaluation.")
    parser.add_argument(
        "command",
        choices=("run", "run-p1p2", "run-p3", "score", "scorecard"),
        help="run all prototypes, run P1/P2, run P3, score outputs, or display the scorecard",
    )
    args = parser.parse_args()
    {
        "run": cmd_run,
        "run-p1p2": cmd_run_p1p2,
        "run-p3": cmd_run_p3,
        "score": cmd_score,
        "scorecard": cmd_scorecard,
    }[args.command]()


if __name__ == "__main__":
    main()