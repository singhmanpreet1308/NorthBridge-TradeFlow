import json 
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DBT_PROJECT = PROJECT_ROOT / "northbridge_dbt"


def run_stage(stage_name, command, cwd=PROJECT_ROOT):
    """Run a pipeline stage and stop if it fails."""

    print(f"\n{'=' * 60}", flush=True)
    print(f"STARTING: {stage_name}", flush=True)
    print(f"{'=' * 60}", flush=True)

    started = datetime.now(timezone.utc)

    result = subprocess.run(
        command,
        cwd=cwd,
        env=os.environ.copy(),
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{stage_name} failed with exit code {result.returncode}"
        )

    completed = datetime.now(timezone.utc)
    duration = (completed - started).total_seconds()

    print(f"\nCOMPLETED: {stage_name}", flush=True)
    print(f"Duration: {duration:.1f} seconds", flush=True)

    # Save pipeline execution timing
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "pipeline_timing.jsonl"

    record = {
        "stage": stage_name,
        "started_at_utc": started.isoformat(),
        "completed_at_utc": completed.isoformat(),
        "duration_seconds": round(duration, 2),
        "status": "SUCCESS"
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")



def main():
    os.environ.setdefault("STORAGE_MODE", "local")

    print("NORTHBRIDGE TRADEFLOW — PIPELINE ORCHESTRATOR")
    print(f"Storage mode: {os.environ['STORAGE_MODE']}")

    run_stage(
        "Trade Validation",
        [sys.executable, "-m", "pipeline.validate"],
    )

    run_stage(
        "Snowflake Ingestion",
        [sys.executable, "ingestion/ingest_to_snowflake.py"],
    )

    run_stage(
        "dbt Transformations and Tests",
        ["dbt", "build", "--project-dir", str(DBT_PROJECT)],
    )

    print("\nPIPELINE STATUS: SUCCESS")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nPIPELINE STATUS: FAILED — {error}", file=sys.stderr)
        sys.exit(1)
