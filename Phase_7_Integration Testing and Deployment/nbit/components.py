"""Adapters that load the real phase components.

Each phase was written as a standalone script folder, so they are put on
sys.path here rather than installed as packages. Nothing in this module
re-implements business logic.
"""

import hashlib
import importlib
import json
import os
import shutil
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from nbit import paths

# Validation must never reach Azure from the test harness.
os.environ.setdefault("STORAGE_MODE", "local")

for folder in (paths.PHASE3_ROOT, paths.PHASE6_ROOT, paths.AMENDMENTS_DIR):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot_tree(root):
    """Map every file under root to its SHA-256 (used for no-change checks)."""
    root = Path(root)
    return {
        str(p.relative_to(root)).replace("\\", "/"): sha256_file(p)
        for p in sorted(root.rglob("*")) if p.is_file()
    }


# 1. Phase 3 - capture, validation and batch publication
def phase3_validate():
    return importlib.import_module("pipeline.validate")


def phase3_local_storage():
    return importlib.import_module("pipeline.local_storage")


def seed_sandbox(sandbox):
    """Create a fresh storage root containing only the raw fixtures."""
    sandbox = Path(sandbox)
    if sandbox.exists():
        shutil.rmtree(sandbox)
    shutil.copytree(paths.RAW_FIXTURES, sandbox / "raw")
    return sandbox


def run_phase3_batch(sandbox):
    """Run the unmodified Phase 3 validate.main() against a sandbox root.

    Returns the captured console log. Phase 3 resolves every path through
    local_storage.BACKUP_ROOT, so pointing it at the sandbox keeps the real
    azure_backup folder untouched.
    """
    storage = phase3_local_storage()
    validate = phase3_validate()

    original_root = storage.BACKUP_ROOT
    storage.BACKUP_ROOT = Path(sandbox)
    log = StringIO()
    try:
        with redirect_stdout(log):
            validate.main()
    finally:
        storage.BACKUP_ROOT = original_root

    return log.getvalue()


def find_batch(sandbox):
    """Return paths of the (single) published batch in a sandbox."""
    audit_dirs = sorted((Path(sandbox) / "curated" / "audit").glob("BATCH-*"))
    if len(audit_dirs) != 1:
        raise RuntimeError(f"Expected one batch, found {len(audit_dirs)}")

    batch_id = audit_dirs[0].name
    root = Path(sandbox)
    return {
        "batch_id": batch_id,
        "curated": root / "curated" / "trades" / batch_id / "validated_trades.csv",
        "quarantine": root / "quarantine" / "trades" / batch_id / "blocked_trades.csv",
        "summary": root / "curated" / "audit" / batch_id / "validation_summary.json",
        "checksums": root / "curated" / "audit" / batch_id / "output_checksums.json",
        "success": root / "curated" / "audit" / batch_id / "_SUCCESS.json",
        "quarantine_root": root / "quarantine" / "trades",
    }


# 2. Phase 4 - approved amendment, revalidation, ingestion checks
def phase4_create_amendment():
    return importlib.import_module("create_amendment")


def phase4_validate_amendment():
    return importlib.import_module("validate_amendment")


def phase4_ingest_amendments():
    return importlib.import_module("ingest_amendments")


def load_approval(path=paths.APPROVAL_FILE):
    return json.loads(Path(path).read_text(encoding="utf-8"))


# 3. Phase 6 - prediction API and AI assistant
def phase6_api(model_dir=None, expected_sha256=None):
    """Import (or re-import) the FastAPI app, optionally for another model."""
    if model_dir is None:
        os.environ.pop("NB_MODEL_DIR", None)
    else:
        os.environ["NB_MODEL_DIR"] = str(model_dir)

    if expected_sha256 is None:
        os.environ.pop("NB_EXPECTED_MODEL_SHA256", None)
    else:
        os.environ["NB_EXPECTED_MODEL_SHA256"] = expected_sha256

    if "app.main" in sys.modules:
        return importlib.reload(sys.modules["app.main"])
    return importlib.import_module("app.main")


def api_client(model_dir=None):
    from fastapi.testclient import TestClient
    return TestClient(phase6_api(model_dir).app)


def predict_via_client(client):
    """Adapter with the same contract as assistant.prediction_client."""
    keys = ["trade_id", "notional_amount", "tenor_years",
            "currency", "product_type", "counterparty_id"]

    def predict(trade):
        response = client.post("/predict", json={k: trade[k] for k in keys})
        if response.status_code != 200:
            return {"status": "error",
                    "message": f"Prediction API returned HTTP {response.status_code}."}
        return {"status": "success", "prediction": response.json()}

    return predict


def assistant():
    return importlib.import_module("assistant.ops_assistant")


def retriever():
    return importlib.import_module("assistant.retriever").KnowledgeRetriever()
