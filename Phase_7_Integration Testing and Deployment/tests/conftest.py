"""Shared fixtures and test-case result collection.

Tests are tagged with @pytest.mark.tc("TC-...") so every result can be
traced to a test case, and through the catalogue to a requirement.
Run with --tc-results PATH to save per-test-case outcomes for the RTM.
"""

import json
import shutil
from collections import defaultdict
from pathlib import Path

import pandas as pd
import pytest

from nbit import components, paths
from nbit.golden_thread import GoldenThread
from nbit.warehouse import Warehouse

_TC_RESULTS = defaultdict(list)


def pytest_addoption(parser):
    parser.addoption("--tc-results", default=None,
                     help="Write per-test-case outcomes to this JSON file.")


def pytest_configure(config):
    config.addinivalue_line("markers", "tc(*ids): test case IDs proven by this test")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    marker = item.get_closest_marker("tc")
    if not marker:
        return
    # Record the call phase, or a setup failure/skip.
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        for tc_id in marker.args:
            _TC_RESULTS[tc_id].append({
                "test": item.nodeid,
                "outcome": report.outcome,
                "seconds": round(report.duration, 3),
            })


def pytest_sessionfinish(session, exitstatus):
    target = session.config.getoption("--tc-results")
    if not target:
        return
    summary = {}
    for tc_id, runs in sorted(_TC_RESULTS.items()):
        outcomes = {r["outcome"] for r in runs}
        status = ("Failed" if "failed" in outcomes
                  else "Not Run" if outcomes == {"skipped"} else "Passed")
        summary[tc_id] = {"status": status, "tests": runs}
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    Path(target).write_text(json.dumps(summary, indent=2), encoding="utf-8")


# Golden thread (run once per session)
@pytest.fixture(scope="session")
def golden(tmp_path_factory):
    thread = GoldenThread(tmp_path_factory.mktemp("golden_thread"))
    thread.result = thread.run()
    return thread


@pytest.fixture(scope="session")
def stage(golden):
    def get(stage_id):
        found = next(s for s in golden.result["stages"] if s["id"] == stage_id)
        assert found["status"] == "PASS", f"{stage_id}: {found.get('detail')}"
        return found["facts"]
    return get


# Independent sandboxes for replay and fault-injection tests
@pytest.fixture
def make_batch(tmp_path):
    """Seed a sandbox, optionally mutate the raw inputs, run Phase 3."""
    def build(mutate=None):
        sandbox = components.seed_sandbox(tmp_path / "storage")
        if mutate:
            mutate(sandbox)
        log = components.run_phase3_batch(sandbox)
        return sandbox, components.find_batch(sandbox), log
    return build


@pytest.fixture
def batch_warehouse(make_batch):
    """Warehouse loaded with the initial batch only (no amendment)."""
    sandbox, batch, _ = make_batch()
    wh = Warehouse()
    wh.load_curated_batch(batch["curated"])
    return wh, batch


@pytest.fixture
def amendment_copy(tmp_path):
    """Writable copies of the committed Phase 4 amendment evidence."""
    target = tmp_path / "amendment"
    target.mkdir()
    files = {
        "csv": paths.AMENDMENT_VALIDATED,
        "audit": paths.AMENDMENT_AUDIT,
        "approval": paths.APPROVAL_FILE,
        "source": paths.AMENDMENT_SOURCE,
    }
    copied = {}
    for key, source in files.items():
        copied[key] = target / source.name
        shutil.copyfile(source, copied[key])
    return copied


@pytest.fixture(scope="session")
def raw_trades():
    return pd.read_csv(paths.RAW_FIXTURES / "trades" / "sample_trades.csv")


@pytest.fixture(scope="session")
def confirmations():
    return pd.read_csv(paths.RAW_FIXTURES / "confirmations" / "independent_confirmations.csv")
