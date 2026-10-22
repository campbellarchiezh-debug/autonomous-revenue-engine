#!/usr/bin/env python3
"""
Master E2E Test Suite Runner for Autonomous Revenue Engine.
Supports running tests by tier (--tier 1|2|3|4|all), structured summary reporting,
and strict exit code semantics (exit 0 on 100% pass of asserted tests).
"""

import sys
import os
import time
import argparse
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

TIER_MODULE_MAP = {
    "1": ("Tier 1 (Feature Coverage)", "tests.e2e.test_tier1_features"),
    "2": ("Tier 2 (Boundary & Corner Cases)", "tests.e2e.test_tier2_boundaries"),
    "3": ("Tier 3 (Cross-Feature Combinations)", "tests.e2e.test_tier3_combinations"),
    "4": ("Tier 4 (Real-World Scenarios)", "tests.e2e.test_tier4_scenarios"),
}

class StructuredTestResult(unittest.TestResult):
    def __init__(self, stream=None, descriptions=None, verbosity=1):
        super().__init__(stream, descriptions, verbosity)
        self.verbosity = verbosity
        self.stream = stream or sys.stdout
        self.success_count = 0
        self.test_records = []
        self._start_time = None

    def startTest(self, test):
        super().startTest(test)
        self._start_time = time.time()
        if self.verbosity >= 2:
            self.stream.write(f"  • {test.id()} ... ")
            self.stream.flush()

    def addSuccess(self, test):
        super().addSuccess(test)
        self.success_count += 1
        elapsed = time.time() - (self._start_time or time.time())
        self.test_records.append((test.id(), "PASS", elapsed, ""))
        if self.verbosity >= 2:
            self.stream.write(f"\033[32mPASS\033[0m ({elapsed:.3f}s)\n")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        elapsed = time.time() - (self._start_time or time.time())
        self.test_records.append((test.id(), "SKIP", elapsed, reason))
        if self.verbosity >= 2:
            self.stream.write(f"\033[33mSKIP\033[0m ({reason})\n")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        elapsed = time.time() - (self._start_time or time.time())
        msg = self._exc_info_to_string(err, test)
        self.test_records.append((test.id(), "FAIL", elapsed, msg))
        if self.verbosity >= 2:
            self.stream.write(f"\033[31mFAIL\033[0m\n")

    def addError(self, test, err):
        super().addError(test, err)
        elapsed = time.time() - (self._start_time or time.time())
        msg = self._exc_info_to_string(err, test)
        self.test_records.append((test.id(), "ERROR", elapsed, msg))
        if self.verbosity >= 2:
            self.stream.write(f"\033[31mERROR\033[0m\n")


def run_tier(tier_key, verbosity=1, failfast=False):
    title, module_name = TIER_MODULE_MAP[tier_key]
    loader = unittest.TestLoader()
    try:
        suite = loader.loadTestsFromName(module_name)
    except Exception as e:
        print(f"Error loading module {module_name}: {e}")
        return None

    result = StructuredTestResult(verbosity=verbosity)
    result.failfast = failfast

    if verbosity >= 1:
        print(f"\n[RUNNING] {title} ({module_name})")
    
    start = time.time()
    suite.run(result)
    duration = time.time() - start

    stats = {
        "tier_key": tier_key,
        "title": title,
        "total": result.testsRun,
        "passed": result.success_count,
        "skipped": len(result.skipped),
        "failed": len(result.failures),
        "errors": len(result.errors),
        "duration": duration,
        "failures_list": result.failures,
        "errors_list": result.errors
    }
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Master E2E Test Suite Runner for Autonomous Revenue Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--tier",
        choices=["1", "2", "3", "4", "all"],
        default="all",
        help="Specify which test tier to execute (default: all)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=1,
        help="Increase output verbosity (-v or -vv)"
    )
    parser.add_argument(
        "--failfast",
        action="store_true",
        help="Stop on first test failure"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("      AUTONOMOUS REVENUE ENGINE — OPAQUE-BOX E2E TEST RUNNER")
    print("=" * 80)
    print(f"Project Root : {PROJECT_ROOT}")
    print(f"Selected Tier: {args.tier.upper()}")
    print(f"Verbosity    : {args.verbose}")

    selected_tiers = ["1", "2", "3", "4"] if args.tier == "all" else [args.tier]
    all_stats = []

    for t_key in selected_tiers:
        stats = run_tier(t_key, verbosity=args.verbose, failfast=args.failfast)
        if stats:
            all_stats.append(stats)
            if args.failfast and (stats["failed"] > 0 or stats["errors"] > 0):
                break

    # Summary Table
    print("\n" + "=" * 80)
    print("                              E2E TEST SUMMARY")
    print("=" * 80)
    header = f"{'Tier':<32} | {'Total':>5} | {'Passed':>6} | {'Skipped':>7} | {'Failed':>6} | {'Errors':>6} | {'Status':>8}"
    print(header)
    print("-" * len(header))

    total_tests = 0
    total_passed = 0
    total_skipped = 0
    total_failed = 0
    total_errors = 0
    total_time = 0.0

    for s in all_stats:
        status_str = "PASS" if (s["failed"] == 0 and s["errors"] == 0) else "FAIL"
        print(f"{s['title']:<32} | {s['total']:>5} | {s['passed']:>6} | {s['skipped']:>7} | {s['failed']:>6} | {s['errors']:>6} | {status_str:>8}")
        total_tests += s["total"]
        total_passed += s["passed"]
        total_skipped += s["skipped"]
        total_failed += s["failed"]
        total_errors += s["errors"]
        total_time += s["duration"]

    print("-" * len(header))
    overall_status = "PASS" if (total_failed == 0 and total_errors == 0) else "FAIL"
    print(f"{'OVERALL TOTALS':<32} | {total_tests:>5} | {total_passed:>6} | {total_skipped:>7} | {total_failed:>6} | {total_errors:>6} | {overall_status:>8}")
    print("=" * 80)
    print(f"Execution completed in {total_time:.3f} seconds.")

    # Detail failures/errors if any
    if total_failed > 0 or total_errors > 0:
        print("\n\033[31mFAILURES & ERRORS SUMMARY:\033[0m")
        for s in all_stats:
            for test, msg in s["failures_list"]:
                print(f"\n[FAILURE] {test.id()}:\n{msg}")
            for test, msg in s["errors_list"]:
                print(f"\n[ERROR] {test.id()}:\n{msg}")
        sys.exit(1)
    else:
        print("\n\033[32m✓ 100% of asserted tests PASSED successfully.\033[0m")
        sys.exit(0)

if __name__ == "__main__":
    main()
