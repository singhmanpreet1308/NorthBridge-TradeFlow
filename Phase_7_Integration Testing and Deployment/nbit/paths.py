"""Repository locations used by the integration suite."""

from pathlib import Path

PHASE7_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE7_ROOT.parent

PHASE3_ROOT = REPO_ROOT / "Phase_3_Data Engineering and Governance"
PHASE4_ROOT = REPO_ROOT / "Phase_4_Analytics_ &_Regulatory Intelligence"
PHASE5_ROOT = REPO_ROOT / "Phase_5_Data Science and Predictive Intelligence"
PHASE6_ROOT = REPO_ROOT / "Phase_6_ML Engineering"

AMENDMENTS_DIR = PHASE4_ROOT / "amendments"
APPROVAL_FILE = AMENDMENTS_DIR / "T1001_Approval.json"
AMENDMENT_SOURCE = AMENDMENTS_DIR / "T1001_v2.csv"
AMENDMENT_VALIDATED = AMENDMENTS_DIR / "validated_output" / "T1001_v2_validated.csv"
AMENDMENT_AUDIT = AMENDMENTS_DIR / "validated_output" / "T1001_v2_audit.json"

MODEL_DIR = PHASE5_ROOT / "notebook" / "models"
PHASE5_T1001_PREDICTIONS = PHASE5_ROOT / "notebook" / "evidence" / "T1001_model_predictions.csv"

FIXTURES_DIR = PHASE7_ROOT / "fixtures"
RAW_FIXTURES = FIXTURES_DIR / "raw"
FIXTURE_MANIFEST = FIXTURES_DIR / "fixture_manifest.json"
EXPECTED_DASHBOARD = FIXTURES_DIR / "expected_dashboard_kpis.json"

MODEL_REGISTRY = PHASE7_ROOT / "ops" / "model_registry.json"
EVIDENCE_DIR = PHASE7_ROOT / "evidence"
TRACEABILITY_DIR = PHASE7_ROOT / "traceability"
DELIVERY_TRACKER = REPO_ROOT / "data" / "Phase_2" / "Delivery_Tracker.xlsx"
