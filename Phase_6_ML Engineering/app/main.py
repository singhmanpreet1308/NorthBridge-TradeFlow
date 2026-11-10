
from pathlib import Path
import json
import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict

# Resolve paths relative to this Python file
PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = (
    PROJECT_ROOT
    / "Phase_5_Data Science and Predictive Intelligence"
    / "notebook"
    / "models"
)

# Load the saved model and metadata
pipeline = joblib.load(
    MODEL_DIR / "rejection_risk_pipeline.joblib"
)

with open(MODEL_DIR / "model_metadata.json", encoding="utf-8") as f:
    metadata = json.load(f)

app = FastAPI(
    title="NorthBridge TradeFlow Prediction API",
    version="1.0.0"
)


# Define the input schema
class TradeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trade_id: str = Field(min_length=1)
    notional_amount: float = Field(gt=0)
    tenor_years: float = Field(gt=0)
    currency: str = Field(min_length=1)
    product_type: str = Field(min_length=1)
    counterparty_id: str = Field(min_length=1)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_name": metadata["model_name"],
        "model_version": metadata["model_version"]
    }


@app.post("/predict")
def predict(trade: TradeInput):
    try:
        trade_data = pd.DataFrame([{
            feature: getattr(trade, feature)
            for feature in metadata["features"]
        }])

        risk_score = float(
            pipeline.predict_proba(trade_data)[0, 1]
        )

        threshold = float(metadata["threshold"])
        prediction = int(risk_score >= threshold)

        return {
            "trade_id": trade.trade_id,
            "risk_score": round(risk_score, 6),
            "risk_band": (
                "Flagged" if prediction == 1 else "Not Flagged"
            ),
            "prediction": prediction,
            "threshold": threshold,
            "model_version": metadata["model_version"]
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Check server logs."
        )
