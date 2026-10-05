import time

from src.prototypes.p1_baseline import run_p1
from src.prototypes.p2_retrieval import run_p2


EXPECTED_ANOMALY = "cashflow_divergence"


def run_test(name, function):
    start = time.perf_counter()

    result = function()

    latency = time.perf_counter() - start

    anomalies = [
        a["type"]
        for a in result["anomalies"]["anomalies"]
    ]

    detected_correctly = EXPECTED_ANOMALY in anomalies

    return {
        "name": name,
        "latency": latency,
        "detected_correctly": detected_correctly,
        "explanation": result["explanation"],
    }


def main():

    print("\nRunning P1...")
    p1 = run_test(
        "P1",
        lambda: run_p1("AAPL"),
    )

    print("Running P2...")
    p2 = run_test(
        "P2",
        lambda: run_p2("AAPL", "320193"),
    )

    print("\n" + "=" * 60)
    print("P1 vs P2")
    print("=" * 60)

    print(
        f"\nP1 anomaly detection: "
        f"{'PASS' if p1['detected_correctly'] else 'FAIL'}"
    )

    print(
        f"P2 anomaly detection: "
        f"{'PASS' if p2['detected_correctly'] else 'FAIL'}"
    )

    print(f"\nP1 latency: {p1['latency']:.2f}s")
    print(f"P2 latency: {p2['latency']:.2f}s")

    print("\n" + "-" * 60)
    print("P1 EXPLANATION")
    print("-" * 60)
    print(p1["explanation"])

    print("\n" + "-" * 60)
    print("P2 EXPLANATION")
    print("-" * 60)
    print(p2["explanation"])


if __name__ == "__main__":
    main()