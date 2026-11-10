
from pathlib import Path
import pandas as pd


# 1. Retrieve quarantined trade history
def get_quarantine_history(trade_id, backup_dir):

    backup_dir = Path(backup_dir)
    files = sorted(
        backup_dir.glob("BATCH-*/blocked_trades.csv")
    )

    if not files:
        raise FileNotFoundError(
            f"No quarantine files found in {backup_dir}"
        )

    records = []

    for file in files:
        df = pd.read_csv(file)

        matches = df.loc[
            df["trade_id"].astype(str).str.strip() == trade_id
        ].copy()

        if matches.empty:
            continue

        matches["batch_id"] = file.parent.name
        matches["evidence_source"] = str(file)

        records.extend(matches.to_dict(orient="records"))

    return {
        "trade_id": trade_id,
        "status": "found" if records else "not_found",
        "validation_events": records,
        "event_count": len(records),
        "distinct_versions": sorted({
            int(record["trade_version"])
            for record in records
        }),
    }


# 2. Retrieve curated trade records
def get_curated_trade(trade_id, curated_file):

    curated_file = Path(curated_file)

    if not curated_file.is_file():
        raise FileNotFoundError(
            f"Curated file not found: {curated_file}"
        )

    # utf-8-sig strips the BOM; Snowflake exports use uppercase column names
    df = pd.read_csv(curated_file, encoding="utf-8-sig")
    df.columns = df.columns.str.strip().str.lower()

    matches = df.loc[
        df["trade_id"].astype(str).str.strip() == trade_id
    ].copy()

    return matches.to_dict(orient="records")


# 3. Combine both sources
def investigate_trade(trade_id, backup_dir, curated_file):

    quarantine = get_quarantine_history(
        trade_id, backup_dir
    )

    curated = get_curated_trade(
        trade_id, curated_file
    )

    all_records = (
        quarantine["validation_events"] + curated
    )

    versions = sorted({
        int(record["trade_version"])
        for record in all_records
    })

    return {
        "trade_id": trade_id,
        "status": "found" if all_records else "not_found",
        "distinct_versions": versions,
        "quarantine_events": quarantine["validation_events"],
        "curated_records": curated,
        "quarantine_event_count": quarantine["event_count"],
        "curated_record_count": len(curated),
    }
