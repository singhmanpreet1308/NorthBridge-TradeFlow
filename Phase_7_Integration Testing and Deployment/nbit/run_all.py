"""Run every Phase 7 check and refresh the evidence folder.

    python -m nbit.run_all                    # tests + golden thread + RTM
    python -m nbit.run_all --update-tracker   # also update Delivery_Tracker.xlsx

Exit code is non-zero if any test or golden-thread stage fails.
"""

import argparse
import subprocess
import sys

from nbit import golden_thread, paths, traceability


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--update-tracker", action="store_true")
    args = parser.parse_args(argv)

    evidence = paths.EVIDENCE_DIR
    evidence.mkdir(parents=True, exist_ok=True)

    print("== 1/3 Integration and UAT test suite ==")
    tests = subprocess.run(
        [sys.executable, "-m", "pytest", "-q",
         f"--junitxml={evidence / 'pytest_junit.xml'}",
         f"--tc-results={evidence / 'tc_results.json'}"],
        cwd=paths.PHASE7_ROOT,
    )

    print("\n== 2/3 Golden thread ==")
    thread = golden_thread.main([])

    print("\n== 3/3 Requirements traceability ==")
    rtm = traceability.main(["--update-tracker"] if args.update_tracker else [])

    ok = tests.returncode == 0 and thread == 0 and rtm == 0
    print(f"\nPHASE 7: {'PASS' if ok else 'FAIL'} "
          f"(tests={tests.returncode}, golden_thread={thread}, rtm={rtm})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
