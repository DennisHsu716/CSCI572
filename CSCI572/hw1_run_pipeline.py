"""
Orchestrates the full HW1 pipeline unattended:
  1. Wait out Yahoo's rate limit.
  2. Debug check: one request, confirm status 200 and a healthy number
     of parsed result containers (retrying with growing backoff if not).
  3. --test check: 3 queries, confirm each returns real results.
  4. Full 100-query scrape (hw1.py) -> hw1.json.
  5. Sanity check hw1.json, then run the analysis script -> hw1.csv.

Every stage is gated on the previous one actually looking healthy, so a
rate-limit or selector break stops the pipeline with a clear message in
pipeline.log instead of silently grinding through 100 broken queries.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from urllib.parse import quote_plus

import requests

from hw1 import HEADERS, SearchEngine, read_queries

SCRAPER_SCRIPT = "hw1.py"
ANALYZE_SCRIPT = "hw1_yahoo_set2_final.py"
QUERY_FILE = "./100QueriesSet2.txt"
RESULTS_FILE = "./hw1.json"

LOG_PATH = "pipeline.log"
_log_file = open(LOG_PATH, "a", encoding="utf-8")


def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    _log_file.write(line + "\n")
    _log_file.flush()


def debug_check():
    url = "https://www.search.yahoo.com/search?p=" + quote_plus("eiffel tower")
    resp = requests.get(url, headers=HEADERS, timeout=10)
    log(f"Debug check status code: {resp.status_code}")
    if resp.status_code != 200:
        return False
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")
    results = SearchEngine.scrape_search_result(soup)
    log(f"Debug check found {len(results)} results (sample: {results[:2]})")
    return len(results) >= 5


def test_check():
    queries = read_queries(QUERY_FILE)[:3]
    ok = True
    for q in queries:
        r = SearchEngine.search(q, sleep=False)
        log(f"Test query {q!r} -> {len(r)} results")
        if len(r) < 3:
            ok = False
        time.sleep(5)
    return ok


def main():
    log("=== Pipeline started ===")

    log("Waiting 20 minutes for Yahoo's rate limit to cool down...")
    time.sleep(20 * 60)

    debug_ok = False
    for attempt, wait_min in enumerate([0, 10, 20], start=1):
        if wait_min:
            log(f"Debug check failed. Waiting {wait_min} more minutes before retry...")
            time.sleep(wait_min * 60)
        log(f"--- Debug check attempt {attempt} ---")
        try:
            if debug_check():
                log("Debug check PASSED.")
                debug_ok = True
                break
        except Exception as e:
            log(f"Debug check error: {e}")

    if not debug_ok:
        log("Debug check FAILED after 3 attempts. Aborting pipeline -- Yahoo "
            "is likely still rate-limiting this IP, or the selector changed "
            "again. Re-run debug.py by hand once you're ready to check.")
        return

    log("--- Running --test check (3 queries) ---")
    try:
        if not test_check():
            log("Test check FAILED (too few results on one or more queries). "
                "Aborting pipeline before the full run.")
            return
    except Exception as e:
        log(f"Test check error: {e}. Aborting pipeline.")
        return
    log("Test check PASSED.")

    log("--- Starting full 100-query scrape (this normally takes 1-1.5 hours, "
        "longer if any queries need backoff retries) ---")
    result = subprocess.run([sys.executable, SCRAPER_SCRIPT])
    if result.returncode != 0:
        log(f"Scraper exited with code {result.returncode}. Aborting before analysis.")
        return
    log("Full scrape completed.")

    with open(RESULTS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    empty = sum(1 for v in data.values() if len(v) == 0)
    log(f"{RESULTS_FILE} has {len(data)} queries, {empty} with 0 results.")
    if empty > len(data) * 0.3:
        log("More than 30% of queries returned 0 results -- likely got "
            "rate-limited partway through. Skipping analysis; inspect "
            f"{RESULTS_FILE} and re-run the affected queries by hand before "
            f"running {ANALYZE_SCRIPT}.")
        return

    log("--- Running Task 2 analysis ---")
    result = subprocess.run([sys.executable, ANALYZE_SCRIPT])
    if result.returncode != 0:
        log(f"Analysis exited with code {result.returncode}.")
        return

    log("=== Pipeline completed successfully. hw1.csv is ready. ===")


if __name__ == "__main__":
    main()
