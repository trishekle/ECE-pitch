import json
import time
from pathlib import Path


TEST_FILE = Path("tests/test_cases.json")
def load_test_cases():
    with open(TEST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def check_detection(result, test_case):
    detected_types = {
        anomaly["type"]
        for anomaly in result.get("anomalies", {}).get("anomalies", [])
    }

    expected_types = set(test_case["expected_anomaly_types"])

    if not expected_types:
        return len(detected_types) == 0

    return bool(detected_types & expected_types)


def evaluate_prototype(prototype_function, ticker="AAPL"):
    test_cases = load_test_cases()

    results = []

    for test_case in test_cases:
        start_time = time.perf_counter()

        try:
            result = prototype_function(ticker)
            success = check_detection(result, test_case)

            error = None

        except Exception as e:
            result = {}
            success = False
            error = str(e)

        elapsed = time.perf_counter() - start_time

        results.append(
            {
                "test_id": test_case["id"],
                "category": test_case["category"],
                "passed": success,
                "latency_seconds": round(elapsed, 2),
                "error": error,
            }
        )

    total = len(results)
    passed = sum(r["passed"] for r in results)

    accuracy = passed / total if total else 0

    return {
        "total_tests": total,
        "passed": passed,
        "accuracy": round(accuracy, 3),
        "results": results,
    }


if __name__ == "__main__":
    # from src.prototypes.p1_baseline import run_p1
    from src.prototypes.p2_retrieval import run_p2

    evaluation = evaluate_prototype(run_p2)

    print("\n" + "=" * 60)
    print("PROTOTYPE 1 — EVALUATION")
    print("=" * 60)

    print(f"\nTests: {evaluation['total_tests']}")
    print(f"Passed: {evaluation['passed']}")
    print(f"Accuracy: {evaluation['accuracy']:.1%}")

    print("\nIndividual results:")

    for result in evaluation["results"]:
        status = "PASS" if result["passed"] else "FAIL"

        print(
            f"{result['test_id']} | "
            f"{status} | "
            f"{result['category']} | "
            f"{result['latency_seconds']}s"
        )