"""
Re-scrape only the handful of queries in hw1.json that came back with 0
results (or fewer than the rest) after the full run, instead of redoing
all 100 queries. Merges the new results back into hw1.json (leaving the
other queries untouched), then regenerates hw1.csv / hw1.txt.
"""

import json
import subprocess
import sys
import time
from datetime import datetime

from hw1 import SearchEngine

RESULTS_FILE = "./hw1.json"
LOG_PATH = "retry_failed.log"
_log_file = open(LOG_PATH, "a", encoding="utf-8")

# Retry any query with fewer results than this.
THRESHOLD = 7

# Same backoff schedule as the main scraper: on 0 results, wait and retry.
BACKOFFS = [0, 180, 360]


def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    _log_file.write(line + "\n")
    _log_file.flush()


def main():
    log("=== Retry-failed started ===")

    with open(RESULTS_FILE, encoding="utf-8") as f:
        results = json.load(f)

    targets = [q for q, v in results.items() if len(v) < THRESHOLD]
    log(f"Found {len(targets)} queries with fewer than {THRESHOLD} results: {targets}")

    if not targets:
        log("Nothing to retry. Exiting.")
        log("=== Retry-failed finished ===")
        return

    log("Waiting 3 minutes before the first request (a debug request was "
        "sent a few minutes ago) ...")
    time.sleep(3 * 60)

    for i, query in enumerate(targets):
        log(f"--- Retrying ({i + 1}/{len(targets)}): {query!r} ---")
        query_results = []
        for attempt, backoff in enumerate(BACKOFFS):
            if backoff:
                log(f"  0 results, backing off {backoff}s before retry...")
                time.sleep(backoff)
            try:
                query_results = SearchEngine.search(
                    query, sleep=(i > 0 and attempt == 0)
                )
            except Exception as e:
                log(f"  Error: {e}")
                query_results = []
            if query_results:
                break

        log(f"  -> got {len(query_results)} results")
        if len(query_results) > len(results[query]):
            results[query] = query_results
            with open(RESULTS_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            log(f"  Updated {RESULTS_FILE} (improved from before).")
        else:
            log("  No improvement over existing result -- keeping the old one.")

    log("--- Regenerating hw1.csv / hw1.txt ---")
    result = subprocess.run([sys.executable, "hw1_yahoo_set2_final.py"])
    log(f"Analysis exited with code {result.returncode}.")

    log("=== Retry-failed finished ===")


if __name__ == "__main__":
    main()
