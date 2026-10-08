
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/phase_1")

trades = pd.read_csv(
    DATA_DIR / "sample_trades.csv",
    dtype=str,
    keep_default_na=False
)

confirmations = trades[[
    "trade_id",
    "counterparty_id",
    "currency",
    "notional_amount",
    "fixed_rate",
    "effective_date",
    "maturity_date",
    "pay_receive_fixed",
]].copy()

confirmations.insert(
    0,
    "confirmation_id",
    [
        f"CONF-{i:04d}"
        for i in range(1, len(confirmations) + 1)
    ]
)

# Independent reference economics for T-1001.
confirmations.loc[
    confirmations["trade_id"] == "T-1001",
    "notional_amount"
] = "10000000.00"

confirmations.to_csv(
    DATA_DIR / "independent_confirmations.csv",
    index=False
)

print("Confirmations:", len(confirmations))

print(
    confirmations.loc[
        confirmations["trade_id"] == "T-1001",
        ["trade_id", "notional_amount"]
    ]
)
