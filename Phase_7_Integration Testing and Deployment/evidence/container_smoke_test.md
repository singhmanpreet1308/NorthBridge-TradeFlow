# TC-OPS-002 — Container smoke test

**Executed:** 2026-11-10, local Docker Engine 29.9.3 (Windows 11), image `northbridge-prediction-api:1.0.0` built from `Phase_6_ML Engineering/Dockerfile` at the repository root. The same checks run in the `container` job of `.github/workflows/ci.yml`.

| Check | Command (abridged) | Result |
| --- | --- | --- |
| Starts with registered checksum pinned | `docker run -p 18000:8000 -e NB_EXPECTED_MODEL_SHA256=29b46e6a…8c8175 …` | Started |
| Health and model identity | `GET /health` | `{"status":"healthy","model_name":"Logistic Regression","model_version":"1.0.0","model_sha256":"29b46e6ab089522e2740a7475a435a83ca7e644e91d9123327e4d597668c8175"}` |
| T-1001 v2 prediction | `POST /predict` (10,000,000 GBP, tenor 10, CP-004) | `{"risk_score":0.078747,"risk_band":"Not Flagged","prediction":0,"threshold":0.1,"model_version":"1.0.0"}` — equals Phase 5 recorded score 0.07874651 |
| Refuses unregistered model | `NB_EXPECTED_MODEL_SHA256=0000` | `RuntimeError: Model checksum mismatch in /app/Phase_5_Data Science and Predictive Intelligence/…` |
| Compose healthcheck command | `python -c "urllib.request.urlopen('http://127.0.0.1:8000/health')…"` inside the container | Exit 0 after ~3 s |

Host port 18000 was used to avoid clashing with other local services; the test containers were removed afterwards.

**Status: Passed**
