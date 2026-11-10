
import os
import requests
import pandas as pd


# Configurable prediction API endpoint
PREDICTION_API_URL = os.getenv(
    "PREDICTION_API_URL",
    "http://127.0.0.1:8000/predict"
)


def prepare_trade_features(trade: dict) -> dict:
    """Prepare the required ML features from a trade record."""

    prepared = trade.copy()

    if "tenor_years" not in prepared or pd.isna(
        prepared["tenor_years"]
    ):

        required_dates = ["effective_date", "maturity_date"]

        missing = [
            field for field in required_dates
            if field not in prepared or pd.isna(prepared[field])
        ]

        if missing:
            raise ValueError(
                f"Missing fields required for tenor: {missing}"
            )

        effective = pd.to_datetime(
            prepared["effective_date"],
            errors="raise"
        )

        maturity = pd.to_datetime(
            prepared["maturity_date"],
            errors="raise"
        )

        tenor = (maturity - effective).days / 365.25

        if tenor <= 0:
            raise ValueError(
                "Maturity date must be after effective date."
            )

        prepared["tenor_years"] = tenor

    return prepared


def predict_trade_risk(trade: dict) -> dict:
    """Call the FastAPI model prediction endpoint."""

    required = [
        "trade_id",
        "notional_amount",
        "tenor_years",
        "currency",
        "product_type",
        "counterparty_id",
    ]

    missing = [
        field for field in required
        if field not in trade or pd.isna(trade[field])
    ]

    if missing:
        return {
            "status": "error",
            "message": f"Missing model features: {missing}",
        }

    payload = {
        field: trade[field]
        for field in required
    }

    try:
        response = requests.post(
            PREDICTION_API_URL,
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

        return {
            "status": "success",
            "prediction": response.json(),
        }

    except requests.Timeout:
        return {
            "status": "error",
            "message": "Prediction API request timed out.",
        }

    except requests.ConnectionError:
        return {
            "status": "error",
            "message": "Cannot connect to the prediction API.",
        }

    except requests.HTTPError as exc:
        status_code = (
            exc.response.status_code
            if exc.response is not None
            else None
        )

        return {
            "status": "error",
            "message": f"Prediction API returned HTTP {status_code}.",
        }

    except requests.RequestException as exc:
        return {
            "status": "error",
            "message": f"Prediction request failed: {type(exc).__name__}",
        }
