import time

from src.prototypes.p1_baseline import run_p1
from src.prototypes.p2_retrieval import run_p2


def run_and_measure(name, function):
    start = time.perf_counter()

    result = function()

    elapsed = time.perf_counter() - start

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    print(f"Latency: {elapsed:.2f} seconds")

    print("\nDetected anomalies:")
    for anomaly in result["anomalies"]["anomalies"]:
        print(
            f"- {anomaly['type']} "
            f"[{anomaly['severity']}]"
        )

    print("\nExplanation:")
    print(result["explanation"])

    return {
        "name": name,
        "latency": elapsed,
        "result": result,
    }


if __name__ == "__main__":

    p1 = run_and_measure(
        "PROTOTYPE 1 — BASELINE",
        lambda: run_p1("AAPL"),
    )

    p2 = run_and_measure(
        "PROTOTYPE 2 — EVIDENCE GROUNDED",
        lambda: run_p2("AAPL", "320193"),
    )

    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)

    print(f"P1 latency: {p1['latency']:.2f}s")
    print(f"P2 latency: {p2['latency']:.2f}s")