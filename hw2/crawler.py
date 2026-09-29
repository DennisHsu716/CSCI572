#!/usr/bin/env python3
"""
CSCI 572 HW2 - Multithreaded web crawler (Python)

LLM usage: this code was written with the help of Claude (Anthropic, Claude Opus 5.5).

Outputs (in --out directory):
  fetch_<site>.csv   URL,Status                                   (every in-site URL we attempted)
  visit_<site>.csv   URL,Size (Bytes),# of Outlinks,Content-Type  (2xx + allowed content types)
  urls_<site>.csv    URL,Indicator                                (every discovered URL, repeats included, OK/N_OK)
  errors_<site>.log  network errors / exceptions (for debugging, not submitted)

Usage:
  python crawler.py --site wsj --max-pages 20000 --threads 7 --delay 1.0
"""

import argparse
import csv
import os
import queue
import re
import sys
import threading
import time
from urllib import robotparser
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


try:
    import lxml  # noqa: F401
    PARSER = "lxml"
except ImportError:
    PARSER = "html.parser"


SITES = {
    "nytimes": "https://www.nytimes.com",
    "wsj": "https://www.wsj.com",
    "foxnews": "https://www.foxnews.com",
    "usatoday": "https://www.usatoday.com",
    "latimes": "https://www.latimes.com",
}


USER_AGENT = "Mozilla/5.0 (compatible; CSCI572-HW2-StudentCrawler/1.0)"


# File types we never want to fetch.
EXCLUDED_EXT = re.compile(
    r".*\.(css|js|mjs|json|xml|rss|atom|txt|mp3|mp4|m4a|m4v|wav|avi|mov|mpeg|mpg|webm|ogg|"
    r"flv|wmv|zip|gz|tgz|rar|7z|tar|bz2|exe|dmg|iso|bin|woff2?|ttf|eot|otf|csv|ics|swf)$",
    re.IGNORECASE,
)


DOC_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


# Tags/attributes from which we extract URLs.
LINK_ATTRS = [
    ("a", "href"),
    ("area", "href"),
    ("link", "href"),
    ("img", "src"),
    ("iframe", "src"),
    ("frame", "src"),
    ("embed", "src"),
]


def allowed_type(ct):
    """
    Only process HTML, image, PDF, and Word document content types.
    """
    return (
        ct == "text/html"
        or ct.startswith("image/")
        or ct in DOC_TYPES
    )


def clean(url):
    """
    HW FAQ:
    Replace commas in URLs so CSV remains well-formed.
    """
    return url.replace(",", "_")


class Crawler:

    def __init__(self, args):

        self.site = args.site
        self.root = args.root or SITES[args.site]

        host = urlparse(self.root).hostname.lower()
        bare = host[4:] if host.startswith("www.") else host

        # Both bare domain and www domain are considered inside.
        self.hosts = {
            bare,
            "www." + bare
        }

        self.max_pages = args.max_pages
        self.max_depth = args.max_depth
        self.num_threads = args.threads
        self.timeout = args.timeout

        self.frontier = queue.Queue()

        self.seen = set()

        self.seen_lock = threading.Lock()
        self.count_lock = threading.Lock()
        self.write_lock = threading.Lock()
        self.rate_lock = threading.Lock()

        self.attempted = 0
        self.visited = 0

        self.next_time = 0.0

        self.done = threading.Event()

        self.local = threading.local()

        # -----------------------------------------------------
        # robots.txt
        # -----------------------------------------------------

        self.robots = robotparser.RobotFileParser()
        self.robots_ok = False

        try:

            r = requests.get(
                urljoin(self.root, "/robots.txt"),
                headers={"User-Agent": USER_AGENT},
                timeout=self.timeout
            )

            if r.status_code == 200:
                self.robots.parse(r.text.splitlines())
                self.robots_ok = True

        except requests.RequestException:
            pass

        crawl_delay = (
            self.robots.crawl_delay(USER_AGENT)
            if self.robots_ok
            else None
        )

        self.delay = max(
            args.delay,
            float(crawl_delay) if crawl_delay else 0.0
        )

        # -----------------------------------------------------
        # Output files
        # -----------------------------------------------------

        os.makedirs(args.out, exist_ok=True)

        p = lambda name: os.path.join(
            args.out,
            f"{name}_{self.site}"
        )

        self.fetch_f = open(
            p("fetch") + ".csv",
            "w",
            newline="",
            encoding="utf-8"
        )

        self.visit_f = open(
            p("visit") + ".csv",
            "w",
            newline="",
            encoding="utf-8"
        )

        self.urls_f = open(
            p("urls") + ".csv",
            "w",
            newline="",
            encoding="utf-8"
        )

        self.err_f = open(
            p("errors") + ".log",
            "w",
            encoding="utf-8"
        )

        self.fetch_w = csv.writer(self.fetch_f)
        self.visit_w = csv.writer(self.visit_f)
        self.urls_w = csv.writer(self.urls_f)

        self.fetch_w.writerow([
            "URL",
            "Status"
        ])

        self.visit_w.writerow([
            "URL",
            "Size (Bytes)",
            "# of Outlinks",
            "Content-Type"
        ])

        self.urls_w.writerow([
            "URL",
            "Indicator"
        ])

    # =========================================================
    # Helpers
    # =========================================================

    def in_site(self, url):

        p = urlparse(url)

        return (
            p.scheme in ("http", "https")
            and (p.hostname or "").lower() in self.hosts
        )

    def should_visit(self, url):

        if not self.in_site(url):
            return False

        if EXCLUDED_EXT.match(
            urlparse(url).path
        ):
            return False

        if (
            self.robots_ok
            and not self.robots.can_fetch(
                USER_AGENT,
                url
            )
        ):
            return False

        return True

    def schedule(self, url, depth):

        if depth > self.max_depth:
            return

        if not self.should_visit(url):
            return

        with self.seen_lock:

            if url in self.seen:
                return

            self.seen.add(url)

        self.frontier.put(
            (url, depth)
        )

    def record_url(self, url):

        with self.write_lock:

            self.urls_w.writerow([
                clean(url),
                "OK" if self.in_site(url) else "N_OK"
            ])

    def log_error(self, url, e):

        with self.write_lock:

            self.err_f.write(
                f"{url}\t"
                f"{type(e).__name__}: {e}\n"
            )

    def session(self):

        s = getattr(
            self.local,
            "s",
            None
        )

        if s is None:

            s = requests.Session()

            s.headers["User-Agent"] = USER_AGENT

            self.local.s = s

        return s

    def wait_turn(self):
        """
        Global politeness delay shared by all threads.
        """

        with self.rate_lock:

            now = time.monotonic()

            t = max(
                now,
                self.next_time
            )

            self.next_time = (
                t + self.delay
            )

        pause = (
            t - time.monotonic()
        )

        if pause > 0:
            time.sleep(pause)

    def reserve(self):

        with self.count_lock:

            if self.attempted >= self.max_pages:
                return False

            self.attempted += 1

            return True

    def release(self):

        with self.count_lock:

            self.attempted -= 1

    def fetch(self, url):

        last = None

        # One retry on network errors.
        for _ in range(2):

            self.wait_turn()

            try:

                return self.session().get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=False
                )

            except requests.RequestException as e:

                last = e

        raise last

    def extract_links(self, base, content):

        try:

            soup = BeautifulSoup(
                content,
                PARSER
            )

        except Exception:

            return []

        # Handle <base href="...">
        b = soup.find(
            "base",
            href=True
        )

        if b:

            try:

                base = urljoin(
                    base,
                    b["href"].strip()
                )

            except ValueError:

                pass

        out = []

        for tag, attr in LINK_ATTRS:

            for el in soup.find_all(tag):

                v = el.get(attr)

                if not v or not isinstance(v, str):
                    continue

                v = v.strip()

                if not v:
                    continue

                if v.startswith(
                    (
                        "#",
                        "javascript:",
                        "mailto:",
                        "tel:",
                        "data:"
                    )
                ):
                    continue

                try:

                    u = urldefrag(
                        urljoin(base, v)
                    )[0]

                except ValueError:

                    continue

                if urlparse(u).scheme in (
                    "http",
                    "https"
                ):

                    out.append(u)

        return out

    # =========================================================
    # Core crawling
    # =========================================================

    def process(self, url, depth):

        # Reserve one fetch attempt.
        if not self.reserve():

            self.done.set()

            return

        # -----------------------------------------------------
        # Fetch
        # -----------------------------------------------------

        try:

            resp = self.fetch(url)

        except Exception as e:

            # Network failure after retry: no HTTP status exists,
            # so it is not written to fetch.csv and the slot is released.
            self.release()

            self.log_error(
                url,
                e
            )

            return

        # -----------------------------------------------------
        # fetch.csv
        # -----------------------------------------------------

        status = resp.status_code

        with self.write_lock:

            self.fetch_w.writerow([
                clean(url),
                status
            ])

        # -----------------------------------------------------
        # Redirect
        # -----------------------------------------------------

        if 300 <= status < 400:

            loc = resp.headers.get(
                "Location"
            )

            if loc:

                try:

                    target = urldefrag(
                        urljoin(
                            url,
                            loc.strip()
                        )
                    )[0]

                except ValueError:

                    return

                # Record redirect target as discovered URL.
                self.record_url(target)

                # Only schedule if it is inside the site.
                self.schedule(
                    target,
                    depth
                )

            return

        # -----------------------------------------------------
        # Non-2xx
        # -----------------------------------------------------

        if not (
            200 <= status < 300
        ):

            return

        # -----------------------------------------------------
        # Content type
        # -----------------------------------------------------

        ct = (
            resp.headers
            .get("Content-Type", "")
            .split(";")[0]
            .strip()
            .lower()
        )

        if not allowed_type(ct):
            return

        # -----------------------------------------------------
        # Extract links
        # -----------------------------------------------------

        if ct == "text/html":

            links = self.extract_links(
                url,
                resp.content
            )

        else:

            links = []

        # -----------------------------------------------------
        # Record discovered URLs
        # -----------------------------------------------------

        for link in links:

            self.record_url(
                link
            )

            self.schedule(
                link,
                depth + 1
            )

        # -----------------------------------------------------
        # visit.csv
        # -----------------------------------------------------

        with self.write_lock:

            self.visit_w.writerow([
                clean(url),
                len(resp.content),
                len(links),
                ct
            ])

            self.visited += 1

    # =========================================================
    # Worker
    # =========================================================

    def worker(self):

        while not self.done.is_set():

            try:

                url, depth = (
                    self.frontier.get(
                        timeout=0.5
                    )
                )

            except queue.Empty:

                continue

            try:

                self.process(
                    url,
                    depth
                )

            except Exception as e:

                self.log_error(
                    url,
                    e
                )

            finally:

                self.frontier.task_done()

    # =========================================================
    # Flush
    # =========================================================

    def flush(self):

        with self.write_lock:

            for f in (
                self.fetch_f,
                self.visit_f,
                self.urls_f,
                self.err_f
            ):

                f.flush()

    # =========================================================
    # Run
    # =========================================================

    def run(self):

        print(
            f"Crawling {self.root} | "
            f"max pages {self.max_pages} | "
            f"depth {self.max_depth} | "
            f"threads {self.num_threads} | "
            f"delay {self.delay}s | "
            f"robots.txt "
            f"{'loaded' if self.robots_ok else 'not found'}",
            flush=True
        )

        # -----------------------------------------------------
        # Seed/root URL
        # -----------------------------------------------------

        with self.seen_lock:

            self.seen.add(
                self.root
            )

        # Record the seed URL in urls.csv.
        self.record_url(
            self.root
        )

        self.frontier.put(
            (self.root, 0)
        )

        # -----------------------------------------------------
        # Start worker threads
        # -----------------------------------------------------

        threads = [
            threading.Thread(
                target=self.worker,
                name=f"crawler-{i + 1}",
                daemon=True
            )
            for i in range(
                self.num_threads
            )
        ]

        for t in threads:
            t.start()

        start = time.time()

        last_report = 0.0

        try:

            while not self.done.is_set():

                time.sleep(1)

                with self.count_lock:

                    reached = (
                        self.attempted
                        >= self.max_pages
                    )

                if (
                    reached
                    or self.frontier.unfinished_tasks == 0
                ):

                    self.done.set()

                self.flush()

                if (
                    time.time()
                    - last_report
                    >= 30
                ):

                    last_report = time.time()

                    print(
                        f"[{(time.time() - start) / 60:6.1f} min] "
                        f"attempted {self.attempted} | "
                        f"visited {self.visited} | "
                        f"queue {self.frontier.qsize()}",
                        flush=True
                    )

        except KeyboardInterrupt:

            print(
                "\nInterrupted, finishing in-flight requests...",
                flush=True
            )

            self.done.set()

        # -----------------------------------------------------
        # Wait for threads
        # -----------------------------------------------------

        for t in threads:
            t.join()

        self.flush()

        # -----------------------------------------------------
        # Close files
        # -----------------------------------------------------

        for f in (
            self.fetch_f,
            self.visit_f,
            self.urls_f,
            self.err_f
        ):

            f.close()

        print(
            f"Done in "
            f"{(time.time() - start) / 60:.1f} min. "
            f"attempted {self.attempted}, "
            f"visited {self.visited}",
            flush=True
        )


def main():

    ap = argparse.ArgumentParser(
        description="CSCI 572 HW2 crawler"
    )

    ap.add_argument(
        "--site",
        required=True,
        choices=SITES.keys()
    )

    ap.add_argument(
        "--root",
        help="override root URL (for local testing only)"
    )

    # HW spec: 20,000 max pages (course page allows 10,000 if too slow).
    ap.add_argument(
        "--max-pages",
        type=int,
        default=20000
    )

    ap.add_argument(
        "--max-depth",
        type=int,
        default=16
    )

    ap.add_argument(
        "--threads",
        type=int,
        default=7
    )

    ap.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="seconds between requests (global, across all threads)"
    )

    ap.add_argument(
        "--timeout",
        type=float,
        default=20.0
    )

    ap.add_argument(
        "--out",
        default=None,
        help="output directory (default: output_<site>)"
    )

    args = ap.parse_args()

    args.out = (
        args.out
        or f"output_{args.site}"
    )

    Crawler(args).run()


if __name__ == "__main__":
    sys.exit(main())