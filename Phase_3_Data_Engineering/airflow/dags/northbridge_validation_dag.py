
from datetime import datetime, timedelta
import subprocess
import sys

from airflow.sdk import dag, task


@dag(
    dag_id="northbridge_trade_validation",
    start_date=datetime(2026, 10, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["northbridge", "phase3", "validation"],
    default_args={
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "execution_timeout": timedelta(minutes=15),
},
)
def northbridge_trade_validation():

    @task
    def run_validation():
        subprocess.run(
            [
                sys.executable,
                "/opt/airflow/northbridge_pipeline/validate.py",
            ],
            check=True,
        )

    run_validation()


northbridge_trade_validation()
