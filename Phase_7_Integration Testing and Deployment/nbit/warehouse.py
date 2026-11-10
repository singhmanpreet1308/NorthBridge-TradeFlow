"""Local SQLite mirror of the Snowflake/dbt layer used in Phases 3-4.

Snowflake is not reachable from CI, so the SQL that ran there is ported
here as closely as SQLite allows. Each object names its source:

    trades_validated              CURATED.TRADES_VALIDATED (Phase 3 load)
    stg_trades_validated          northbridge_dbt/models/staging/stg_trades_validated.sql
    int_current_trades            northbridge_dbt/models/intermediate/int_current_trades.sql
    simulated_reporting_outcomes  Phase 4 "Simulated Reporting_Outcome_SQL.txt"
    kpis()                        Phase 4 "KPI_SQL.txt"

Differences from Snowflake are deliberate and limited to syntax
(EXCLUDE, DATEADD, COUNT_IF and :: casts have no SQLite equivalent).
"""

import sqlite3
from datetime import datetime, timedelta, timezone

import pandas as pd

TRADE_KEY = ["trade_id", "trade_version"]

VIEWS = """
CREATE VIEW stg_trades_validated AS
SELECT *
FROM trades_validated
WHERE validation_status = 'PASS';

CREATE VIEW int_current_trades AS
SELECT *
FROM (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY trade_id
            ORDER BY trade_version DESC, validated_at_utc DESC
        ) AS version_rank
    FROM stg_trades_validated
)
WHERE version_rank = 1;

CREATE TABLE simulated_reporting_outcomes (
    submission_id        TEXT,
    trade_id             TEXT,
    trade_version        INTEGER,
    submission_timestamp TEXT,
    reporting_status     TEXT,
    rejection_reason     TEXT,
    processed_at         TEXT
);
"""

# Ported from "Simulated Reporting_Outcome_SQL.txt". Outcomes are positional
# (every 10th current trade by trade_id is rejected), not rule-based.
SIMULATED_REPORTING_INSERT = """
INSERT INTO simulated_reporting_outcomes (
    submission_id, trade_id, trade_version, submission_timestamp,
    reporting_status, rejection_reason, processed_at
)
SELECT
    'SIM-' || trade_id || '-V' || trade_version,
    trade_id,
    trade_version,
    :submitted_at,
    CASE WHEN ROW_NUMBER() OVER (ORDER BY trade_id) % 10 = 0
         THEN 'REJECTED' ELSE 'ACCEPTED' END,
    CASE WHEN ROW_NUMBER() OVER (ORDER BY trade_id) % 10 = 0
         THEN 'DEMO_REPORT_REJECT' ELSE NULL END,
    :processed_at
FROM int_current_trades t
WHERE NOT EXISTS (
    SELECT 1
    FROM simulated_reporting_outcomes r
    WHERE r.trade_id = t.trade_id
      AND r.trade_version = t.trade_version
      AND r.submission_id = 'SIM-' || t.trade_id || '-V' || t.trade_version
);
"""


class Warehouse:

    def __init__(self, path=":memory:"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._created = False

    # 1. Loading
    def _create(self, columns):
        cols = ", ".join(f'"{c}"' for c in columns)
        self.conn.execute(f"CREATE TABLE trades_validated ({cols})")
        self.conn.executescript(VIEWS)
        self.columns = list(columns)
        self._created = True

    def load_curated_batch(self, curated_csv):
        """Initial batch load (Phase 3 ingest_to_snowflake equivalent)."""
        df = pd.read_csv(curated_csv)
        if not self._created:
            self._create(df.columns)
        df.to_sql("trades_validated", self.conn, if_exists="append", index=False)
        return len(df)

    def load_amendment(self, columns, row):
        """Insert one verified amendment row.

        Applies the same pre-checks as Phase 4 ingest_amendments.ingest():
        schema match, no existing trade/version, no reused validation run.
        """
        actual = [c.lower() for c in columns]
        if len(actual) != 26 or set(actual) != set(self.columns):
            raise ValueError("CSV and Snowflake schemas do not match.")

        version = int(row["trade_version"])

        if self.scalar(
            "SELECT COUNT(*) FROM trades_validated "
            "WHERE trade_id = ? AND trade_version = ?",
            (row["trade_id"], version),
        ):
            raise ValueError("Trade version already exists in Snowflake.")

        if self.scalar(
            "SELECT COUNT(*) FROM trades_validated WHERE validation_run_id = ?",
            (row["validation_run_id"],),
        ):
            raise ValueError("Validation run ID already exists.")

        values = []
        for column in columns:
            value = row[column]
            if value == "":
                value = None
            elif column in ("trade_version",):
                value = int(value)
            elif column in ("notional_amount", "fixed_rate"):
                value = float(value)
            values.append(value)

        placeholders = ", ".join("?" * len(columns))
        names = ", ".join(f'"{c}"' for c in actual)

        with self.conn:
            self.conn.execute(
                f"INSERT INTO trades_validated ({names}) VALUES ({placeholders})",
                values,
            )
            if self.scalar(
                "SELECT COUNT(*) FROM trades_validated "
                "WHERE trade_id = ? AND trade_version = ?",
                (row["trade_id"], version),
            ) != 1:
                raise RuntimeError("Post-insertion verification failed.")

    # 2. Simulated reporting
    def run_simulated_reporting(self, now=None):
        """Create simulated submissions for eligible current trades.

        Returns the number of new submissions (0 on replay).
        """
        now = now or datetime.now(timezone.utc)
        with self.conn:
            cursor = self.conn.execute(SIMULATED_REPORTING_INSERT, {
                "submitted_at": (now - timedelta(seconds=5)).isoformat(),
                "processed_at": now.isoformat(),
            })
        return cursor.rowcount

    # 3. Queries
    def scalar(self, sql, params=()):
        return self.conn.execute(sql, params).fetchone()[0]

    def rows(self, sql, params=()):
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def current_trade(self, trade_id):
        found = self.rows(
            "SELECT * FROM int_current_trades WHERE trade_id = ?", (trade_id,)
        )
        return found[0] if found else None

    def submissions(self, trade_id=None):
        if trade_id:
            return self.rows(
                "SELECT * FROM simulated_reporting_outcomes WHERE trade_id = ?",
                (trade_id,),
            )
        return self.rows("SELECT * FROM simulated_reporting_outcomes ORDER BY trade_id")

    def kpis(self, validation_summary):
        """Dashboard KPIs, ported from Phase 4 KPI_SQL.txt."""
        current = self.rows("""
            SELECT
                COUNT(DISTINCT trade_id) AS total_trades,
                COUNT(*) AS current_rows,
                SUM(CASE WHEN currency = 'GBP' THEN notional_amount ELSE 0 END)
                    AS total_notional_gbp,
                SUM(trade_status = 'AMENDED') AS amended_trades,
                SUM(validation_status = 'PASS') AS validated_trades,
                SUM(validation_status = 'BLOCK') AS blocked_current_trades,
                ROUND(100.0 * SUM(validation_status = 'PASS')
                      / NULLIF(COUNT(*), 0), 2) AS current_pass_rate_pct
            FROM int_current_trades
        """)[0]

        reporting = self.rows("""
            SELECT
                COUNT(*) AS total_submissions,
                SUM(reporting_status = 'ACCEPTED') AS accepted,
                SUM(reporting_status = 'REJECTED') AS rejected,
                ROUND(100.0 * SUM(reporting_status = 'REJECTED')
                      / NULLIF(COUNT(*), 0), 2) AS simulated_reject_rate_pct
            FROM simulated_reporting_outcomes
        """)[0]

        total = validation_summary["total_trades"]

        return {
            **current,
            **reporting,
            "initial_quarantine_rate_pct": round(
                100.0 * validation_summary["quarantine_records"] / total, 2
            ),
            "no_amendment_rate_pct": round(
                100.0 * (current["total_trades"] - current["amended_trades"])
                / current["total_trades"], 2
            ),
            "status_distribution": {
                r["trade_status"]: r["trade_count"] for r in self.rows("""
                    SELECT trade_status, COUNT(DISTINCT trade_id) AS trade_count
                    FROM int_current_trades GROUP BY trade_status
                """)
            },
            "counterparty_notional_gbp": {
                r["counterparty_id"]: r["total_notional_gbp"] for r in self.rows("""
                    SELECT counterparty_id,
                           SUM(notional_amount) AS total_notional_gbp
                    FROM int_current_trades WHERE currency = 'GBP'
                    GROUP BY counterparty_id ORDER BY total_notional_gbp DESC
                """)
            },
            "duplicate_trade_versions": self.rows("""
                SELECT trade_id, trade_version, COUNT(*) AS record_count
                FROM trades_validated
                GROUP BY trade_id, trade_version HAVING COUNT(*) > 1
            """),
        }
