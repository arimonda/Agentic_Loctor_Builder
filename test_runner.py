"""
Test Runner for Loctor Builder
================================
Standalone test script that validates the system end-to-end.

Usage:
    python test_runner.py                    # Run all tests
    python test_runner.py --test quick       # Quick validation only
    python test_runner.py --test healing     # Healing test only
    python test_runner.py --test multipage   # Multi-page test only
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.config_manager import ConfigManager
from core.auditor import Auditor


def setup_logging():
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/test_runner.log", encoding="utf-8"),
        ],
    )


def print_header(text: str):
    width = 70
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width)


def print_result(label: str, value, color_code: str = ""):
    print(f"  {label:<25} {value}")


async def run_single_test(config: ConfigManager, script_path: str, test_name: str) -> dict:
    """Run a single test script and return results."""
    print_header(f"TEST: {test_name}")
    print(f"  Script: {script_path}")
    print(f"  Provider: {config.active_provider}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    ConfigManager.reset()
    config = ConfigManager("config.json")

    auditor = Auditor(config)

    elements_log = []

    def on_element(result):
        status = result.status.value.upper()
        icon = {"PASSED": "[OK]", "HEALED": "[FX]", "FAILED": "[!!]", "SKIPPED": "[--]"}
        marker = icon.get(status, "[??]")
        msg = f"    {marker} {status:>7} | {result.element_name} ({result.original_locator.selector_string})"
        print(msg)
        elements_log.append({
            "name": result.element_name,
            "status": status,
            "locator": result.original_locator.selector_string,
        })

    def on_page(page_name, url):
        print(f"\n  --- Page: {page_name} ({url}) ---")

    auditor.set_callbacks(on_element_audited=on_element, on_page_started=on_page)

    start = time.time()
    try:
        report = await auditor.run_audit(script_path)
        elapsed = time.time() - start

        print(f"\n  {'─' * 50}")
        print_result("Total Elements:", report.total_elements)
        print_result("Passed:", report.passed)
        print_result("Healed:", report.healed)
        print_result("Failed:", report.failed)
        print_result("Success Rate:", f"{report.success_rate:.1f}%")
        print_result("Duration:", f"{elapsed:.1f}s")
        print_result("Provider:", report.ai_provider_used)

        return {
            "test_name": test_name,
            "script": script_path,
            "total": report.total_elements,
            "passed": report.passed,
            "healed": report.healed,
            "failed": report.failed,
            "success_rate": report.success_rate,
            "duration_seconds": round(elapsed, 1),
            "provider": report.ai_provider_used,
            "elements": elements_log,
            "status": "COMPLETED",
        }
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n  [ERROR] Test failed: {e}")
        return {
            "test_name": test_name,
            "script": script_path,
            "status": "ERROR",
            "error": str(e),
            "duration_seconds": round(elapsed, 1),
        }


async def test_quick_validation(config: ConfigManager) -> dict:
    """Test 1: Quick validation with all-valid locators."""
    return await run_single_test(
        config,
        "input/scripts/01_herokuapp_login.json",
        "Quick Validation (All Valid Locators)",
    )


async def test_healing(config: ConfigManager) -> dict:
    """Test 2: Broken locators to trigger AI healing."""
    return await run_single_test(
        config,
        "input/scripts/02_herokuapp_broken_locators.json",
        "Self-Healing (Broken Locators with Gemini AI)",
    )


async def test_multi_page(config: ConfigManager) -> dict:
    """Test 3: Multi-page navigation audit."""
    return await run_single_test(
        config,
        "input/scripts/03_herokuapp_multi_page.json",
        "Multi-Page Navigation Audit",
    )


async def test_mixed_strategies(config: ConfigManager) -> dict:
    """Test 4: Mixed locator strategies."""
    return await run_single_test(
        config,
        "input/scripts/04_herokuapp_mixed_strategies.json",
        "Mixed Locator Strategies (ID, CSS, XPath, Name)",
    )


async def main(test_filter: str = "all"):
    setup_logging()

    print_header("LOCTOR BUILDER - TEST SUITE")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Filter:  {test_filter}")

    config = ConfigManager("config.json")
    print(f"  Provider: {config.active_provider}")
    print(f"  Model: {config.get_provider_config()['model']}")

    results = []
    total_start = time.time()

    test_map = {
        "quick": [test_quick_validation],
        "healing": [test_healing],
        "multipage": [test_multi_page],
        "mixed": [test_mixed_strategies],
        "all": [test_quick_validation, test_multi_page, test_mixed_strategies],
    }

    tests = test_map.get(test_filter, test_map["all"])

    for test_fn in tests:
        ConfigManager.reset()
        config = ConfigManager("config.json")
        result = await test_fn(config)
        results.append(result)

    total_elapsed = time.time() - total_start

    print_header("FINAL SUMMARY")
    print(f"  {'Test Name':<45} {'Status':<12} {'Pass':<6} {'Heal':<6} {'Fail':<6} {'Rate'}")
    print(f"  {'─' * 90}")

    for r in results:
        if r["status"] == "COMPLETED":
            print(
                f"  {r['test_name']:<45} {r['status']:<12} "
                f"{r['passed']:<6} {r['healed']:<6} {r['failed']:<6} "
                f"{r['success_rate']:.0f}%"
            )
        else:
            print(f"  {r['test_name']:<45} {r['status']:<12} {r.get('error', '')}")

    print(f"\n  Total Duration: {total_elapsed:.1f}s")
    print(f"  Tests Run: {len(results)}")

    report_path = Path("logs/reports") / f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "run_time": datetime.now().isoformat(),
            "total_duration": total_elapsed,
            "test_filter": test_filter,
            "results": results,
        }, f, indent=2)
    print(f"  Report: {report_path}")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Loctor Builder Test Runner")
    parser.add_argument("--test", default="all", choices=["all", "quick", "healing", "multipage", "mixed"])
    args = parser.parse_args()
    asyncio.run(main(args.test))
