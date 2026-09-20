"""
HW1 Task 1: Scrape top-10 Yahoo results for each query in 100QueriesSet2.txt
and save them to hw1.json.

Selector + redirect-unwrap logic verified against a live Yahoo response
on 2026-09 (Yahoo's HTML structure can still change again later, so if
you start getting 0 results again, re-run debug.py to check).

Run a quick 3-query test first with:
    python3 hw1_scraper.py --test
before committing to the full run (each query sleeps 10-100s, so the
full 100-query run takes roughly 1-1.5 hours).
"""

import json
import re
import time
import sys
from random import randint
from urllib.parse import quote_plus, unquote

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.yahoo.com/",
}

REQUEST_TIMEOUT = 10  # seconds


def unwrap_yahoo_redirect(href):
    """Yahoo wraps organic result links in a redirect like:
    https://r.search.yahoo.com/_ylt=.../RU=<url-encoded-real-url>/RK=.../RS=...
    Extract and decode the real target URL. Falls back to the raw href
    if the pattern isn't present."""
    m = re.search(r"/RU=([^/]+)/", href)
    if m:
        return unquote(m.group(1))
    return href


class SearchEngine:

    @staticmethod
    def search(query, sleep=True):
        if sleep:
            time.sleep(randint(10, 100))

        url = "https://www.search.yahoo.com/search?p=" + quote_plus(query)
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(response.text, "html.parser")
        return SearchEngine.scrape_search_result(soup)

    @staticmethod
    def scrape_search_result(soup):
        # Organic result containers currently carry both "algo" and
        # "algo-sr" classes (verified via debug.py).
        containers = soup.find_all(
            "div",
            attrs={"class": lambda c: c and {"algo", "algo-sr"}.issubset(c.split())}
        )

        results = []
        for container in containers:
            link_tag = container.find("a", href=True)
            if not link_tag:
                continue
            real_url = unwrap_yahoo_redirect(link_tag["href"])
            if real_url not in results:
                results.append(real_url)
            if len(results) == 10:
                break

        return results


def read_queries(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def run(queries, output_file):
    results = {}
    print("Number of queries:", len(queries))

    # If a query comes back with 0 results, back off and retry a couple of
    # times before giving up on it -- a 0-result page usually means Yahoo
    # rate-limited that one request rather than the selector being wrong.
    backoffs = [0, 180, 360]  # seconds to wait before each attempt

    for i, query in enumerate(queries):
        print("=" * 40)
        print(f"Query {i + 1}/{len(queries)}: {query}")

        query_results = []
        for attempt, backoff in enumerate(backoffs):
            if backoff:
                print(f"  -> 0 results, backing off {backoff}s before retry...")
                time.sleep(backoff)
            try:
                query_results = SearchEngine.search(
                    query, sleep=(i > 0 and attempt == 0)
                )
            except Exception as e:
                print("Error:", e)
                query_results = []
            if query_results:
                break

        results[query] = query_results
        print("Results collected:", len(results[query]))
        if len(results[query]) == 0:
            print("  -> WARNING: 0 results after retries. Selector may have "
                  "changed again, or Yahoo may still be rate-limiting you.")

        # Save progress after every query so a crash/block doesn't lose
        # everything scraped so far.
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    print("=" * 40)
    print("Task 1 completed. Generated:", output_file)


if __name__ == "__main__":
    query_file = "./100QueriesSet2.txt"
    output_file = "./hw1.json"

    all_queries = read_queries(query_file)

    if "--test" in sys.argv:
        print("Running in TEST mode: first 3 queries only, no sleep.\n")
        test_results = {}
        for q in all_queries[:3]:
            print("Query:", q)
            test_results[q] = SearchEngine.search(q, sleep=False)
            print("  ->", test_results[q])
        print("\nIf these came back empty, run debug.py to check the "
              "selector again before running the full pass.")
    else:
        run(all_queries, output_file)