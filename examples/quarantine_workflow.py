from data_reliability import DataTier, ReliabilityPolicy, ReliabilityScanner, ValidationEvidence, decision_to_document


scanner = ReliabilityScanner()
policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_1)

rows = [
    {"id": "a", "temperature": 21.4, "unit": "celsius"},
    {"id": "b", "temperature": None, "unit": "celsius"},
]

trusted = []
quarantine = []

for row in rows:
    reliable = scanner.scan(
        row,
        source_id=row["id"],
        evidence=ValidationEvidence(cryptographic_verification=1.0, calibration=0.95),
        required_fields=["temperature", "unit"],
    )
    decision = policy.assess(reliable.reliability)
    if decision.accepted:
        trusted.append(reliable)
    else:
        quarantine.append({"row": row, "decision": decision_to_document(decision)})

assert len(trusted) == 1
assert quarantine[0]["decision"]["accepted"] is False
