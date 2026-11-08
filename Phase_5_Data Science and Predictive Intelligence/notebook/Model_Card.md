
# NorthBridge TradeFlow — Model Card

## 1. Model Overview

| Attribute                | Description                        |
| ------------------------ | ---------------------------------- |
| Model Name               | OTC Trade Rejection Risk Predictor |
| Model Version            | 1.0.0                              |
| Selected Algorithm       | Logistic Regression                |
| Framework                | scikit-learn                       |
| Prediction Task          | Binary Classification              |
| Target                   | `simulated_rejected`             |
| Classification Threshold | 0.10                               |
| Model Status             | Synthetic Proof of Concept         |

**Objective:** Estimate the probability of a simulated OTC trade reporting rejection using information available before reporting submission.

The model is intended to demonstrate risk-based trade review, not to make autonomous regulatory reporting decisions.

## 2. Dataset and Features

**Training source:** Reproducible synthetic GBP interest rate swap history.

| Dataset                 | Records |
| ----------------------- | ------: |
| Total synthetic history |   2,000 |
| Training                |   1,400 |
| Validation              |     300 |
| Held-out test           |     300 |

**Target distribution (full dataset):**

- Accepted: 1,811 (90.55%)
- Rejected: 189 (9.45%)

**Model features:**

- `notional_amount`
- `tenor_years`
- `currency`
- `product_type`
- `counterparty_id`

**Preprocessing:**

- StandardScaler for numerical features.
- OneHotEncoder for categorical features.
- Preprocessing fitted only on training data.

Random seed: `42`.

## 3. Temporal Split and Leakage Controls

| Split      | Date range                 |
| ---------- | -------------------------- |
| Training   | 01 Jan 2024 – 29 May 2025 |
| Validation | 30 May 2025 – 12 Sep 2025 |
| Test       | 12 Sep 2025 – 31 Dec 2025 |

The model uses trade execution time as its demonstration prediction timestamp.

**Leakage controls:**

- `simulated_rejected` excluded from predictors.
- `report_outcome_timestamp` excluded from predictors.
- Reporting outcomes occur after the prediction timestamp.
- Trade IDs do not overlap between data partitions.
- Preprocessing fitted on training data only.
- Validation data used for model and threshold selection.
- Held-out test data used for final evaluation.

The listed date ranges overlap on 12 September at date-level precision; chronological timestamp ordering was verified in the notebook.

## 4. Model Selection

Evaluated configurations included Dummy Classifier, Logistic Regression, XGBoost, balanced variants, Random Forest and CatBoost.

Original Logistic Regression was selected based on its validation F1-score, PR-AUC, interpretability and relative simplicity.

**Selected model validation results:**

| Metric                     |  Value |
| -------------------------- | -----: |
| PR-AUC (Average Precision) | 0.2328 |
| Precision                  | 0.2209 |
| Recall                     | 0.5588 |
| F1-score                   | 0.3167 |
| Selected threshold         |   0.10 |

The threshold was selected using validation data, balancing precision and recall through F1-score.

## 5. Final Held-Out Test Results

| Metric                     | Result |
| -------------------------- | -----: |
| Accuracy                   | 68.00% |
| PR-AUC (Average Precision) | 0.1376 |
| Precision                  | 16.16% |
| Recall                     | 55.17% |
| F1-score                   | 0.2500 |

**Confusion matrix:**

|                 | Predicted Accepted | Predicted Rejected |
| --------------- | -----------------: | -----------------: |
| Actual Accepted |                188 |                 83 |
| Actual Rejected |                 13 |                 16 |

**Interpretation:**

The model detected 16 of 29 simulated rejected trades, missed 13, and generated 83 false alerts.

Test performance was weaker than validation performance, particularly in precision and PR-AUC. The model demonstrates limited predictive discrimination and is not suitable for production risk decisions.

The test dataset was not used to retune the selected model or threshold.

## 6. SHAP Explainability

SHAP was used to explain predictions from the selected Logistic Regression model.

**Main findings:**

- Notional amount and swap tenor had the largest average absolute contributions.
- Counterparty classification had a smaller influence.
- Currency and product type contributed little because they were constant in synthetic training data.

SHAP contributions are expressed in log-odds rather than percentage-point changes in probability.

These explanations describe relationships learned from synthetic data and do not establish real-world regulatory rejection causes.

## 7. T-1001 Prediction Evidence

T-1001 represents a 10-year GBP interest rate swap with an incorrect captured notional followed by an approved correction.

| Attribute                | Version 1       | Version 2       |
| ------------------------ | --------------- | --------------- |
| Trade ID                 | T-1001          | T-1001          |
| Notional                 | £100,000,000   | £10,000,000    |
| Tenor                    | 10 years        | 10 years        |
| Counterparty             | CP-004          | CP-004          |
| Model Version            | 1.0.0           | 1.0.0           |
| Predicted Risk           | ~18.3%          | ~7.9%           |
| Threshold Classification | Review Required | Below Threshold |

*Displayed probabilities are approximated from the SHAP log-odds plots; replace them with the exact saved `predict_proba` outputs before final acceptance.*

The change in predicted risk is primarily explained by the difference in notional amount.

The separate `DEMO_NOTIONAL_MISMATCH` validation rule identifies the original trade discrepancy. The machine learning model does not replace deterministic validation.

The lower model score after correction is an observed demonstration result, not a guaranteed outcome of amendments.

## 8. Model Limitations

1. Synthetic rejection labels were generated using assumed probability rules rather than real regulatory outcomes.
2. The synthetic sample contains only 2,000 trades and approximately 9.45% rejected outcomes.
3. Notional and tenor relationships reflect simulation assumptions, not proven industry rejection risk factors.
4. Model precision is low, creating considerable false alerts.
5. The model has not been calibrated or validated on real labelled rejection data.
6. Training uses a fixed GBP IRS product classification, limiting generalisation to other swap types.
7. Real CME GBP OIS data lacks counterparty identifiers and verified reporting rejection labels, preventing direct accuracy evaluation.

## 9. Intended Use and Restrictions

**Intended use:**

- Demonstrate pre-submission predictive risk scoring.
- Support simulated trade review prioritisation.
- Provide explainable model predictions.
- Integrate with the NorthBridge ML API and operations assistant.

**Not intended for:**

- Live trading decisions.
- Automated regulatory submissions.
- Production rejection prediction.
- Autonomous trade correction or approval.

## 10. Model Artifacts

- `models/rejection_risk_pipeline.joblib`
- `models/model_metadata.json`
- `evidence/T1001_model_predictions.csv`
- SHAP feature importance, beeswarm and waterfall evidence.
- `01_Rejection_Risk_Model.ipynb`
- `02_Risk_Prediction_check.ipynb`

**Conclusion:** Logistic Regression was retained because it offered the strongest overall validation performance among the tested configurations. The implementation demonstrates a reproducible and explainable predictive modelling workflow, while the held-out evaluation confirms that real-world predictive validity remains unestablished.
