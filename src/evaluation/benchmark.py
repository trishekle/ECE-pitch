import json
import statistics
import time

from src.prototypes.p1_baseline import run_p1
from src.prototypes.p2_retrieval import run_p2


TICKER = "AAPL"
CIK = "320193"
TRIALS = 3


def benchmark(name, function):
    times = []

    print(f"\n=== {name} ===")

    for i in range(1, TRIALS + 1):
        print(f"Trial {i}/{TRIALS}...")

        start = time.perf_counter()

        try:
            function(TICKER, CIK) if name == "P2" else function(TICKER)

            elapsed = time.perf_counter() - start
            times.append(elapsed)

            print(f"  {elapsed:.2f}s")

        except Exception as e:
            print(f"  ERROR: {e}")

    if not times:
        return None

    return {
        "trials": [round(t, 2) for t in times],
        "mean": round(statistics.mean(times), 2),
        "min": round(min(times), 2),
        "max": round(max(times), 2),
        "stdev": round(statistics.stdev(times), 2)
        if len(times) > 1
        else 0.0,
    }


def main():
    print("=" * 60)
    print("P1 vs P2 LATENCY BENCHMARK")
    print("=" * 60)
    print(f"Ticker: {TICKER}")
    print(f"Trials per prototype: {TRIALS}")

    p1_results = benchmark("P1", run_p1)
    p2_results = benchmark("P2", run_p2)

    results = {
        "ticker": TICKER,
        "trials_per_prototype": TRIALS,
        "P1": p1_results,
        "P2": p2_results,
    }

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    for name, data in results.items():
        if name in ("P1", "P2") and data:
            print(f"\n{name}")
            print(f"  Trials: {data['trials']}")
            print(f"  Mean:   {data['mean']:.2f}s")
            print(f"  Min:    {data['min']:.2f}s")
            print(f"  Max:    {data['max']:.2f}s")
            print(f"  Std:    {data['stdev']:.2f}s")

    with open("latency_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nSaved results to latency_results.json")


if __name__ == "__main__":
    main()