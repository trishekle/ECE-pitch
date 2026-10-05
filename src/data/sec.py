import requests


HEADERS = {
    "User-Agent": "FinancialAnomalyDetector research@example.com"
}


def get_sec_company_facts(cik: str):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
    )

    response.raise_for_status()

    return response.json()


def get_relevant_facts(cik: str):
    data = get_sec_company_facts(cik)

    facts = data.get("facts", {}).get("us-gaap", {})

    relevant = {}

    for name in [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "OperatingIncomeLoss",
        "NetIncomeLoss",
        "NetCashProvidedByUsedInOperatingActivities",
        "LongTermDebtNoncurrent",
    ]:
        if name in facts:
            relevant[name] = facts[name]

    return relevant


if __name__ == "__main__":
    # Apple CIK
    facts = get_relevant_facts("320193")

    print("Retrieved SEC facts:")
    for name in facts:
        print("-", name)