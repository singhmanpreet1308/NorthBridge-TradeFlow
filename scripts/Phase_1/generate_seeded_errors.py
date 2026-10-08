
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/phase_1")

baseline = pd.read_csv(
    DATA_DIR / "sample_trades.csv",
    dtype=str,
    keep_default_na=False
)

# Never modify the baseline DataFrame.
seeded = baseline.copy(deep=True)

# Trade ID -> field changes and expected validation rule.
scenarios = {
    "T-1001": {
        "changes": {},
        "rule": "DEMO_NOTIONAL_MISMATCH",
        "description": "Captured notional differs from confirmation",
    },
    "T-1004": {
        "changes": {"counterparty_id": ""},
        "rule": "DQ-009",
        "description": "Missing mandatory counterparty",
    },
    "T-1008": {
        "changes": {"notional_amount": "-5000000.00"},
        "rule": "DQ-004",
        "description": "Negative notional",
    },
    "T-1012": {
        "changes": {"currency": "USD"},
        "rule": "DQ-005",
        "description": "Non-GBP currency",
    },
    "T-1016": {
        "changes": {"maturity_date": "2020-01-01"},
        "rule": "DQ-006",
        "description": "Maturity precedes effective date",
    },
    "T-1020": {
        "changes": {"fixed_rate": "1.250000"},
        "rule": "DQ-007",
        "description": "Fixed rate outside demonstration range",
    },
    "T-1024": {
        "changes": {"pay_receive_fixed": "UNKNOWN"},
        "rule": "DQ-008",
        "description": "Invalid fixed-leg direction",
    },
    "T-1028": {
        "changes": {"trade_id": ""},
        "rule": "DQ-001",
        "description": "Missing trade ID",
    },
    "T-1032": {
        "changes": {"floating_rate_index": ""},
        "rule": "DQ-009",
        "description": "Missing floating-rate index",
    },
    "T-1040": {
        "changes": {"notional_amount": "0.00"},
        "rule": "DQ-004",
        "description": "Zero notional",
    },
}

error_rows = []
manifest = []

for trade_id, scenario in scenarios.items():

    match = seeded.loc[
        seeded["trade_id"] == trade_id
    ]

    if len(match) != 1:
        raise ValueError(
            f"Expected exactly one baseline record: {trade_id}"
        )

    row = match.iloc[0].copy()

    for field, value in scenario["changes"].items():
        row[field] = value

    error_rows.append(row.to_dict())

    manifest.append({
        "fixture_trade_id": trade_id,
        "expected_rule": scenario["rule"],
        "description": scenario["description"],
        "expected_outcome": "BLOCK",
    })

# One record per seeded scenario.
errors_df = pd.DataFrame(
    error_rows,
    columns=baseline.columns
)

manifest_df = pd.DataFrame(manifest)

errors_df.to_csv(
    DATA_DIR / "seeded_errors.csv",
    index=False
)

manifest_df.to_csv(
    DATA_DIR / "seeded_error_manifest.csv",
    index=False
)

print("Seeded records:", len(errors_df))
print("Manifest entries:", len(manifest_df))
print("Baseline records:", len(baseline))
