
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

    duration = (datetime.now(timezone.utc) - started).total_seconds()

    print(f"\nCOMPLETED: {stage_name}", flush=True)
    print(f"Duration: {duration:.1f} seconds", flush=True)


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
