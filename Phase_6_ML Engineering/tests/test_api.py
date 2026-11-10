
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_TRADE = {
    "trade_id": "TEST-001",
    "notional_amount": 10000000,
    "tenor_years": 10,
    "currency": "GBP",
    "product_type": "IRS",
    "counterparty_id": "CP-001"
}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["model_version"] == "1.0.0"


def test_valid_prediction():
    response = client.post("/predict", json=VALID_TRADE)
    assert response.status_code == 200

    result = response.json()
    assert result["trade_id"] == "TEST-001"
    assert 0 <= result["risk_score"] <= 1
    assert result["prediction"] in [0, 1]
    assert result["model_version"] == "1.0.0"


def test_missing_field():
    trade = VALID_TRADE.copy()
    del trade["counterparty_id"]

    response = client.post("/predict", json=trade)
    assert response.status_code == 422


def test_negative_notional():
    trade = VALID_TRADE.copy()
    trade["notional_amount"] = -10000000

    response = client.post("/predict", json=trade)
    assert response.status_code == 422


def test_invalid_data_type():
    trade = VALID_TRADE.copy()
    trade["notional_amount"] = "invalid_amount"

    response = client.post("/predict", json=trade)
    assert response.status_code == 422
