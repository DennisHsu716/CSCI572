"""
Carefully (single-shot, well-spaced requests) checks whether adding the
Yahoo `&n=30` parameter (per the HW1 FAQ #3) returns more organic results
per page than the default. If it clearly helps, patches hw1.py's search
URL to always include it and re-launches the full pipeline (which itself
already does the debug/test checkpoints before the full 100-query run).

Only ever sends TWO requests total, 45s apart, after a 20-minute cooldown --
rapid back-to-back testing is what re-triggers Yahoo's rate limiting.
"""

import subprocess
import sys
import time
from datetime import datetime
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from hw1 import HEADERS, SearchEngine

LOG_PATH = "n30_test.log"
_log_file = open(LOG_PATH, "a", encoding="utf-8")


def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    _log_file.write(line + "\n")
    _log_file.flush()


def fetch_count(url, label):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
    except Exception as e:
        log(f"{label}: request error: {e}")
        return None, None
    if resp.status_code != 200:
        log(f"{label}: status {resp.status_code} (not 200)")
        return resp.status_code, None
    soup = BeautifulSoup(resp.text, "html.parser")
    results = SearchEngine.scrape_search_result(soup)
    log(f"{label}: status 200, {len(results)} results")
    return 200, len(results)


def run():
    log("=== n=30 test started ===")
    if "--skip-cooldown" in sys.argv:
        log("Skipping cooldown wait (--skip-cooldown): caller confirmed it's "
            "been a long time since the last request.")
    else:
        log("Waiting 20 minutes to make sure Yahoo's rate limit is fully clear...")
        time.sleep(20 * 60)

    query = "eiffel tower"
    plain_url = "https://www.search.yahoo.com/search?p=" + quote_plus(query)
    n30_url = plain_url + "&n=30"

    status_plain, count_plain = fetch_count(plain_url, "PLAIN")
    if status_plain != 200:
        log("Plain request failed -- Yahoo still appears blocked. Aborting "
            "n=30 test; not touching the working scraper. Try again later.")
        return

    log("Waiting 45s before the second (n=30) request...")
    time.sleep(45)

    status_n30, count_n30 = fetch_count(n30_url, "N=30")
    if status_n30 != 200:
        log("n=30 request failed (plain worked, n=30 didn't) -- treating "
            "n=30 as NOT usable. Keeping the scraper as-is.")
        return

    log(f"Comparison: plain={count_plain} results, n=30={count_n30} results")

    if count_n30 > count_plain:
        log("n=30 gives MORE results. Patching hw1.py to always use it, "
            "then launching the full pipeline re-run.")
        with open("hw1.py", "r", encoding="utf-8") as f:
            src = f.read()
        old = 'url = "https://www.search.yahoo.com/search?p=" + quote_plus(query)'
        new = 'url = "https://www.search.yahoo.com/search?p=" + quote_plus(query) + "&n=30"'
        if old not in src:
            log(f"ERROR: could not find expected line to patch in hw1.py: {old!r}. "
                "Aborting patch; scraper left unchanged.")
            return
        src = src.replace(old, new)
        with open("hw1.py", "w", encoding="utf-8") as f:
            f.write(src)
        log("hw1.py patched. Launching full pipeline re-run now...")

        result = subprocess.run([sys.executable, "hw1_run_pipeline.py"])
        log(f"Pipeline re-run exited with code {result.returncode}. See pipeline.log for details.")
    else:
        log("n=30 does NOT give more results than the default page "
            "(or gave the same/fewer). Leaving hw1.py and hw1.json/hw1.csv "
            "as they are -- no re-run needed.")


def main():
    try:
        run()
    finally:
        # Always leave this sentinel behind, on every exit path (including
        # exceptions), so anything waiting on this log file doesn't hang.
        log("=== n=30 test finished ===")


if __name__ == "__main__":
    main()
