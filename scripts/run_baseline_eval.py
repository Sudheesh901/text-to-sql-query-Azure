import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database import execute_query
from text_to_sql import question_to_sql

EVALUATION_FILE = ROOT / "evaluation" / "golden_questions.json"


def is_single_select(sql: str) -> bool:
    statements = [
        statement.strip()
        for statement in sql.split(";")
        if statement.strip()
    ]
    return len(statements) == 1 and statements[0].lower().startswith("select")


def load_cases():
    with EVALUATION_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def run_case(case, run_live=False):
    start = time.perf_counter()
    response = question_to_sql(case["question"])
    elapsed_seconds = time.perf_counter() - start

    if case["should_clarify"]:
        passed = response.startswith("CLARIFY:")
        return {
            "id": case["id"],
            "passed": passed,
            "message": response,
            "seconds": elapsed_seconds,
        }

    if response.startswith(("CLARIFY:", "INVALID_SQL:")):
        return {
            "id": case["id"],
            "passed": False,
            "message": response,
            "seconds": elapsed_seconds,
        }

    if not is_single_select(response):
        return {
            "id": case["id"],
            "passed": False,
            "message": f"Unsafe SQL generated: {response}",
            "seconds": elapsed_seconds,
        }

    if not run_live:
        return {
            "id": case["id"],
            "passed": True,
            "message": "Valid SELECT generated; database execution skipped.",
            "seconds": elapsed_seconds,
        }

    try:
        results = execute_query(response)
        returned_columns = {column.lower() for column in results.columns}
        expected_columns = {
            column.lower() for column in case["expected_columns"]
        }
        missing_columns = expected_columns - returned_columns

        if missing_columns:
            return {
                "id": case["id"],
                "passed": False,
                "message": f"Missing expected columns: {sorted(missing_columns)}",
                "seconds": elapsed_seconds,
            }

        return {
            "id": case["id"],
            "passed": True,
            "message": f"Executed successfully: {len(results)} row(s) returned.",
            "seconds": elapsed_seconds,
        }
    except Exception as error:
        return {
            "id": case["id"],
            "passed": False,
            "message": f"Database error: {error}",
            "seconds": elapsed_seconds,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="Execute generated SQL against the configured database.",
    )
    args = parser.parse_args()

    cases = load_cases()
    results = [run_case(case, run_live=args.live) for case in cases]

    passed_count = 0
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        print(
            f"[{status}] {result['id']} "
            f"({result['seconds']:.2f}s) - {result['message']}"
        )
        passed_count += result["passed"]

    print(f"\nResult: {passed_count}/{len(results)} evaluation cases passed.")

    if passed_count != len(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()