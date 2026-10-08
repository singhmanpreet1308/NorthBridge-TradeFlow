
from pathlib import Path
from datetime import datetime, timedelta, timezone
import csv
import random

random.seed(42)

OUTPUT_DIR = Path("data/phase_1")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "sample_trades.csv"

FIELDS = [
    "trade_id",
    "trade_version",
    "source_system",
    "source_trade_ref",
    "capture_timestamp",
    "trade_date",
    "counterparty_id",
    "product_type",
    "currency",
    "notional_amount",
    "fixed_rate",
    "floating_rate_index",
    "pay_receive_fixed",
    "effective_date",
    "maturity_date",
    "payment_frequency",
    "trade_status",
    "amendment_reason",
    "created_by",
    "record_timestamp",
]

base_date = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)

trades = []

for i in range(1, 51):
    trade_id = f"T-{1000 + i}"

    capture_dt = base_date + timedelta(
        days=random.randint(0, 20),
        minutes=random.randint(0, 480),
    )

    trade_date = capture_dt.date()
    effective_date = trade_date + timedelta(days=2)

    tenor_years = random.choice([2, 3, 5, 7, 10])

    # Calendar-year addition; avoids approximating
    # every year as exactly 365 days.
    try:
        maturity_date = effective_date.replace(
            year=effective_date.year + tenor_years
        )
    except ValueError:
        maturity_date = effective_date.replace(
            year=effective_date.year + tenor_years,
            day=28,
        )

    notional = random.choice([
        1_000_000,
        2_500_000,
        5_000_000,
        10_000_000,
        25_000_000,
        50_000_000,
    ])

    if trade_id == "T-1001":
        notional = 100_000_000
        effective_date = trade_date + timedelta(days=2)
        maturity_date = effective_date.replace(
            year=effective_date.year + 10
        )

    fixed_rate = round(random.uniform(0.025, 0.055), 6)

    trade = {
        "trade_id": trade_id,
        "trade_version": 1,
        "source_system": "OMS",
        "source_trade_ref": f"OMS-{1000 + i}",
        "capture_timestamp": capture_dt.isoformat(),
        "trade_date": trade_date.isoformat(),
        "counterparty_id": f"CP-{random.randint(1, 10):03d}",
        "product_type": "GBP_IRS",
        "currency": "GBP",
        "notional_amount": f"{notional:.2f}",
        "fixed_rate": f"{fixed_rate:.6f}",
        "floating_rate_index": "SONIA",
        "pay_receive_fixed": random.choice(["PAY", "RECEIVE"]),
        "effective_date": effective_date.isoformat(),
        "maturity_date": maturity_date.isoformat(),
        "payment_frequency": "ANNUAL",
        "trade_status": "CAPTURED",
        "amendment_reason": "",
        "created_by": f"trader_{random.randint(1, 5):02d}",
        "record_timestamp": capture_dt.isoformat(),
    }

    trades.append(trade)

with OUTPUT_FILE.open(
    "w", newline="", encoding="utf-8"
) as file:
    writer = csv.DictWriter(file, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(trades)

print(f"Created: {OUTPUT_FILE}")
print(f"Trade records: {len(trades)}")
print(f"Columns: {len(FIELDS)}")
print(f"T-1001 notional: {trades[0]['notional_amount']}")
