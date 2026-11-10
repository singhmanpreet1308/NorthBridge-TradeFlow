
from pathlib import Path

from assistant.trade_lookup import investigate_trade
from assistant.prediction_client import (
    prepare_trade_features,
    predict_trade_risk
)


# ==========================================
# 1. PROJECT PATHS
# ==========================================

PROJECT_ROOT = Path(
    r"D:\STUDY\Data_Science_Courses\PROJECTS\14.NorthBridge TradeFlow\NorthBridge-TradeFlow"
)

backup_dir = (
    PROJECT_ROOT
    / "Phase_3_Data Engineering and Governance"
    / "azure_backup"
    / "quarantine"
    / "trades"
)

curated_file = (
    PROJECT_ROOT
    / "Phase_6_ML Engineering"
    / "data"
    / "t1001_curated_v2.csv"
)


# ==========================================
# 2. RETRIEVE TRADE HISTORY
# ==========================================

result = investigate_trade(
    trade_id="T-1001",
    backup_dir=backup_dir,
    curated_file=curated_file
)

print("\n=== TRADE INVESTIGATION ===")

print("Trade ID:", result["trade_id"])
print("Status:", result["status"])
print("Distinct Versions:", result["distinct_versions"])
print("Quarantine Events:", result["quarantine_event_count"])
print("Curated Records:", result["curated_record_count"])


# ==========================================
# 3. DISPLAY CURATED TRADE
# ==========================================

for record in result["curated_records"]:
    print(
        "Version:", record["trade_version"],
        "| Notional:", record["notional_amount"],
        "| Status:", record["validation_status"]
    )


# ==========================================
# 4. PREPARE MODEL FEATURES
# ==========================================

if not result["curated_records"]:
    raise ValueError("No curated trade found for prediction.")

trade_v2 = result["curated_records"][0]

prepared_trade = prepare_trade_features(trade_v2)

print("\n=== PREPARED MODEL FEATURES ===")

print("Notional Amount:", prepared_trade["notional_amount"])
print("Tenor Years:", prepared_trade["tenor_years"])
print("Currency:", prepared_trade["currency"])
print("Product Type:", prepared_trade["product_type"])
print("Counterparty:", prepared_trade["counterparty_id"])


# ==========================================
# 5. CALL FASTAPI PREDICTION SERVICE
# ==========================================

print("\n=== T-1001 PREDICTION ===")

prediction_result = predict_trade_risk(prepared_trade)

print(prediction_result)


# ==========================================
# 6. DISPLAY MODEL PREDICTION
# ==========================================

if prediction_result["status"] == "success":

    prediction = prediction_result["prediction"]

    print("\n=== MODEL RESULT ===")

    print("Trade ID:", prediction["trade_id"])
    print("Risk Score:", prediction["risk_score"])
    print("Risk Band:", prediction["risk_band"])
    print("Prediction:", prediction["prediction"])
    print("Threshold:", prediction["threshold"])
    print("Model Version:", prediction["model_version"])

else:
    print("\nPrediction failed:")
    print(prediction_result["message"])
