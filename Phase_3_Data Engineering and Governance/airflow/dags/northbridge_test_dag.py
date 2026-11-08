
from datetime import datetime

from airflow.sdk import dag, task


@dag(
    dag_id="northbridge_test_pipeline",
    start_date=datetime(2026, 10, 1),
    schedule=None,
    catchup=False,
    tags=["northbridge", "phase3", "testing"],
)
def northbridge_test_pipeline():

    @task
    def check_environment():
        print("NorthBridge TradeFlow Airflow environment is working.")
        return "ENVIRONMENT_OK"

    @task
    def check_pipeline():
        print("NorthBridge TradeFlow pipeline orchestration test.")
        return "PIPELINE_OK"

    @task
    def confirm_success():
        print("Airflow DAG executed successfully.")
        return "SUCCESS"

    environment = check_environment()
    pipeline = check_pipeline()
    success = confirm_success()

    environment >> pipeline >> success


northbridge_test_pipeline()
