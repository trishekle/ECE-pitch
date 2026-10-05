from src.detection.anomalies import ANOMALY_THRESHOLDS


# Each scenario:
# (name, metric, value, expected_anomaly)
SCENARIOS = [
    ("Revenue spike", "revenue_growth", 0.35, True),
    ("Revenue normal", "revenue_growth", 0.10, False),
    ("Margin drop", "margin_change", -0.10, True),
    ("Margin normal", "margin_change", 0.02, False),
    ("Cash flow divergence", "cashflow_divergence", 0.30, True),
    ("Cash flow normal", "cashflow_divergence", 0.10, False),
    ("Debt increase", "debt_change", 0.40, True),
    ("Debt normal", "debt_change", 0.10, False),
    ("Market divergence", "market_financial_gap", 0.40, True),
    ("Market normal", "market_financial_gap", 0.10, False),
]


def detector_rule(metric, value):
    """
    Apply the same threshold logic used by the anomaly detector.
    """

    threshold = ANOMALY_THRESHOLDS[metric]

    return abs(value) >= threshold


def calculate_metrics(results):
    tp = sum(
        predicted and expected
        for _, expected, predicted in results
    )

    tn = sum(
        not predicted and not expected
        for _, expected, predicted in results
    )

    fp = sum(
        predicted and not expected
        for _, expected, predicted in results
    )

    fn = sum(
        not predicted and expected
        for _, expected, predicted in results
    )

    accuracy = (tp + tn) / len(results)

    precision = tp / (tp + fp) if (tp + fp) else 0

    recall = tp / (tp + fn) if (tp + fn) else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def main():
    results = []

    print("\n" + "=" * 60)
    print("ANOMALY DETECTOR EVALUATION")
    print("=" * 60)

    for name, metric, value, expected in SCENARIOS:

        predicted = detector_rule(metric, value)

        results.append(
            (name, expected, predicted)
        )

        status = "PASS" if predicted == expected else "FAIL"

        print(
            f"{status} | "
            f"{name:<25} | "
            f"expected={expected} | "
            f"predicted={predicted}"
        )

    metrics = calculate_metrics(results)

    print("\n" + "=" * 60)
    print("METRICS")
    print("=" * 60)

    print(f"Accuracy : {metrics['accuracy']:.2%}")
    print(f"Precision: {metrics['precision']:.2%}")
    print(f"Recall   : {metrics['recall']:.2%}")
    print(f"F1 Score : {metrics['f1']:.2%}")

    print("\nConfusion matrix counts:")
    print(f"True Positives : {metrics['tp']}")
    print(f"True Negatives : {metrics['tn']}")
    print(f"False Positives: {metrics['fp']}")
    print(f"False Negatives: {metrics['fn']}")


if __name__ == "__main__":
    main()