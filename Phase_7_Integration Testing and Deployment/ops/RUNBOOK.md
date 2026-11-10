# NorthBridge TradeFlow — Operations Runbook

Scope: the components that run on a workstation or CI runner — the local validation pipeline, the prediction API, the AI Operations Assistant and the Phase 7 test harness. Azure, Snowflake and Power BI are covered in their phase folders and are **not** needed for anything below.

All commands run from the repository root unless stated. The project's Python environment is the conda env `NorthBridge_TradeFlow` (Python 3.12).

---

## 1. Components and ports

| Component | Entry point | Port | Needs |
| --- | --- | --- | --- |
| Validation pipeline (Phase 3) | `python -m pipeline.validate` (in the Phase 3 folder) | — | `STORAGE_MODE=local` + `azure_backup/raw/*`, or Azure CLI login |
| Prediction API (Phase 6) | `uvicorn app.main:app` or Docker | 8000 | Phase 5 model artifact |
| AI Operations Assistant UI | `streamlit run chat_ui.py` | 8501 | Prediction API, `EURI_API_KEY` |
| Integration harness (Phase 7) | `python -m nbit.run_all` | — | Nothing external |

## 2. Configuration

| Variable | Used by | Default | Notes |
| --- | --- | --- | --- |
| `STORAGE_MODE` | Phase 3 validate | `azure` | Set `local` to read `azure_backup/`. The Phase 7 harness forces `local`. |
| `NB_MODEL_DIR` | Prediction API | Phase 5 `notebook/models` | Folder holding `rejection_risk_pipeline.joblib` + `model_metadata.json`. Used for rollback. |
| `NB_EXPECTED_MODEL_SHA256` | Prediction API | unset (compose sets it) | API refuses to start if the artifact's SHA-256 differs. |
| `PREDICTION_API_URL` | Assistant | `http://127.0.0.1:8000/predict` | |
| `EURI_API_KEY`, `EURI_BASE_URL`, `EURI_MODEL` | Assistant | — / Euri / `gpt-4.1-mini` | Put in `Phase_6_ML Engineering/.env` (git-ignored). Template: `.env.example`. |
| `MODEL_TAG` | docker compose | `1.0.0` | Image tag to run. |

Secrets never go in the repository. `.gitignore` excludes `.env`, `*.pem`, `profiles.yml` and `azure_backup/`.

## 3. Startup

**Prediction API (Docker, recommended)**

```bash
docker compose -f "Phase_7_Integration Testing and Deployment/ops/docker-compose.yml" up -d --build
docker compose -f "Phase_7_Integration Testing and Deployment/ops/docker-compose.yml" ps   # wait for "healthy"
curl http://localhost:8000/health
```

**Prediction API (local Python)**

```bash
cd "Phase_6_ML Engineering"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**AI Operations Assistant** (API must be up first)

```bash
cd "Phase_6_ML Engineering"
streamlit run chat_ui.py          # http://localhost:8501
```

**Full integration check** (no services needed — it starts the API in-process)

```bash
cd "Phase_7_Integration Testing and Deployment"
python -m nbit.run_all
```

## 4. Teardown

```bash
docker compose -f "Phase_7_Integration Testing and Deployment/ops/docker-compose.yml" down
# also delete the image:  ... down --rmi local
```

Stop `uvicorn` / `streamlit` with Ctrl+C. The Phase 7 harness works in a temporary folder that is deleted automatically; it never writes to `azure_backup/` (use `--workdir PATH` to keep a sandbox for inspection).

## 5. Monitoring signals

| Signal | Where | Healthy | Action if not |
| --- | --- | --- | --- |
| API liveness | `GET /health` → `status` | `healthy`, HTTP 200 | Check `docker logs northbridge-prediction-api` |
| Model identity | `GET /health` → `model_version`, `model_sha256` | Equal to `ops/model_registry.json` → `current` | Treat as an unapproved deployment → rollback (§6) |
| Container health | `docker compose ps` | `healthy` | 3 failed probes → container marked unhealthy and restarted |
| Prediction errors | API HTTP 500 rate | 0 | Server logs; request validation errors are 422 and expected for bad input |
| Prediction drift | Share of trades scored `Flagged` | Phase 5 baseline: 4 of 28 real CME trades flagged, all outside training ranges | Review inputs outside the synthetic training ranges before trusting scores |
| Batch completion | `curated/audit/<BATCH>/_SUCCESS.json` | Present, `status=COMPLETED` | Missing marker + outputs present = partial batch; pipeline refuses to overwrite (§7) |
| Batch integrity | `verify_output_checksums` on replay | `All stored output checksums verified.` | `SHA-256 mismatch` = stored output changed; investigate, do not re-run over it |
| Batch counts | `validation_summary.json` | `curated + quarantine = total`, manifest 10/10 | Pipeline stops itself if counts or the seeded-defect self-test change |
| Assistant grounding | `warnings`, `unknown_citations` in each answer | Both empty | Answer cites something it was not given — do not act on it |
| Pipeline timing | `logs/pipeline_timing.jsonl` (orchestrator) | 50-trade batch ≤ 60 s (NFR-001) | Measured locally ≈ 1 s; see `evidence/golden_thread/` |

## 6. Rollback to a known model version

The known-good versions and their checksums are in [`model_registry.json`](model_registry.json). Today only **1.0.0** exists (commit `849d7d6`, SHA-256 `29b46e6a…8c8175`).

**Docker**

```bash
# 1. Stop the faulty release
docker compose -f "Phase_7_Integration Testing and Deployment/ops/docker-compose.yml" down

# 2. Restore the registered artifact (if the files in the repo were changed)
git checkout 849d7d6 -- "Phase_5_Data Science and Predictive Intelligence/notebook/models"

# 3. Start the known version with its checksum pinned
MODEL_TAG=1.0.0 \
NB_EXPECTED_MODEL_SHA256=29b46e6ab089522e2740a7475a435a83ca7e644e91d9123327e4d597668c8175 \
docker compose -f "Phase_7_Integration Testing and Deployment/ops/docker-compose.yml" up -d --build

# 4. Verify
curl -s http://localhost:8000/health   # model_version 1.0.0, model_sha256 29b46e6a...
```

**Local Python**: point `NB_MODEL_DIR` at a folder holding the registered artifact, set `NB_EXPECTED_MODEL_SHA256`, restart `uvicorn`, check `/health`.

If the checksum does not match, the API **refuses to start** (`RuntimeError: Model checksum mismatch`) rather than serving an unknown model.

This procedure is tested by `TC-OPS-001` (`tests/test_05_prediction_assistant.py`): a relabelled candidate is served, then rolled back to 1.0.0 with the checksum pinned. Because only one model has been trained, the candidate is a copy with a new version label, not a different model.

**Registering a new version**: train, save to a new folder, add an entry to `model_registry.json` (version, sha256, metrics, git commit), run `python -m nbit.run_all`, then change `current`. Keep the old entry — it is the rollback target.

## 7. Failure and replay behaviour

Observed in Phase 7 (each is a test in `tests/test_06_nfr_failure_replay.py` or `test_02`):

| Situation | Behaviour | Test |
| --- | --- | --- |
| Same batch re-run | `Batch status: SKIPPED`; every file byte-identical | TC-CAP-003 |
| Stored output edited after publication | Replay stops with `SHA-256 mismatch`; file left as found | TC-NFR-005 |
| Crash before `_SUCCESS.json` | Replay stops with `Partial batch detected`; nothing overwritten | TC-NFR-005 |
| Duplicate / conflicting trade ID in source | Whole batch aborts (`Baseline validation counts changed`); nothing published | TC-CAP-004 |
| A trade loses its confirmation | Whole batch aborts (same control) | TC-VAL-003 |
| Amendment loaded twice | Refused: `Trade version already exists` | TC-AMD-004 |
| Reporting re-run | 0 new submissions | TC-RPT-003 |
| Prediction API down | Assistant still answers and states `NOT AVAILABLE` for model risk | TC-AI-006 |

**Recovery from a partial batch**: compare the outputs that exist with `validation_summary.json` and the source checksum, move the partial batch folder aside (do not delete — it is evidence), and re-run. Because the batch ID is derived from the input checksums and policy version, the re-run writes to the same batch ID.

**Known limitation**: the pipeline's 49-PASS / 1-BLOCK baseline control is hard-coded for the demonstration dataset. Any new legitimate exception aborts the batch instead of quarantining one trade. Replace it with a reconciliation check (`curated + quarantine = total`) before using other data.
