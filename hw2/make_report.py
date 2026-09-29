#!/usr/bin/env python3
"""
CSCI 572 HW2 - Build CrawlReport_<site>.txt from the crawler's CSV output,
then run the grading-rubric consistency checks.

LLM usage: this code was written with the help of Claude (Anthropic, Claude Opus 5.5).

Usage:
  python make_report.py \
      --site wsj \
      --dir output_wsj \
      --name "Your Name" \
      --usc-id 1234567890 \
      --threads 7
"""

import argparse
import csv
import os
import sys
from collections import Counter
from http import HTTPStatus


csv.field_size_limit(10**8)


SITE_DOMAINS = {
    "nytimes": "nytimes.com",
    "wsj": "wsj.com",
    "foxnews": "foxnews.com",
    "usatoday": "usatoday.com",
    "latimes": "latimes.com",
}


def read_rows(path):

    with open(
        path,
        newline="",
        encoding="utf-8"
    ) as f:

        r = csv.reader(f)

        # Skip header.
        next(r, None)

        return [
            row
            for row in r
            if row
        ]


def status_label(code):

    try:

        return (
            f"{code} "
            f"{HTTPStatus(code).phrase}"
        )

    except ValueError:

        return str(code)


def main():

    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--site",
        required=True,
        choices=SITE_DOMAINS.keys()
    )

    ap.add_argument(
        "--dir",
        default=None,
        help="directory with the CSVs (default: output_<site>)"
    )

    ap.add_argument(
        "--name",
        required=True
    )

    ap.add_argument(
        "--usc-id",
        required=True
    )

    ap.add_argument(
        "--threads",
        type=int,
        default=7
    )

    # HW spec: 20,000 max pages (course page allows 10,000 if too slow).
    ap.add_argument(
        "--max-pages",
        type=int,
        default=20000,
        help="the MAX pages you crawled with"
    )

    ap.add_argument(
        "--note",
        default="",
        help="optional note appended to the report"
    )

    args = ap.parse_args()

    d = (
        args.dir
        or f"output_{args.site}"
    )

    # ---------------------------------------------------------
    # Read CSV files
    # ---------------------------------------------------------

    fetch = read_rows(
        os.path.join(
            d,
            f"fetch_{args.site}.csv"
        )
    )

    visit = read_rows(
        os.path.join(
            d,
            f"visit_{args.site}.csv"
        )
    )

    urls = read_rows(
        os.path.join(
            d,
            f"urls_{args.site}.csv"
        )
    )

    # =========================================================
    # Fetch Statistics
    # =========================================================

    attempted = len(fetch)

    numeric_statuses = []

    failed_network = 0

    for row in fetch:

        status = row[1]

        if status == "FAILED":

            failed_network += 1

        else:

            try:

                numeric_statuses.append(
                    int(status)
                )

            except ValueError:

                failed_network += 1

    succeeded = sum(
        1
        for s in numeric_statuses
        if 200 <= s < 300
    )

    failed = (
        attempted
        - succeeded
    )

    # =========================================================
    # Outgoing URLs
    # =========================================================

    total_extracted = sum(
        int(row[2])
        for row in visit
    )

    # Use separate sets rather than storing only
    # the last indicator for each URL.

    unique_urls = set()

    unique_in_urls = set()

    unique_out_urls = set()

    for row in urls:

        url = row[0]

        indicator = row[1]

        unique_urls.add(
            url
        )

        if indicator == "OK":

            unique_in_urls.add(
                url
            )

        elif indicator == "N_OK":

            unique_out_urls.add(
                url
            )

    unique_total = len(
        unique_urls
    )

    unique_in = len(
        unique_in_urls
    )

    unique_out = len(
        unique_out_urls
    )

    # =========================================================
    # Status Codes
    # =========================================================

    status_counts = sorted(
        Counter(
            numeric_statuses
        ).items()
    )

    # =========================================================
    # File Sizes
    # =========================================================

    bins = [0] * 5

    for row in visit:

        size = int(
            row[1]
        )

        if size < 1024:

            bins[0] += 1

        elif size < 10 * 1024:

            bins[1] += 1

        elif size < 100 * 1024:

            bins[2] += 1

        elif size < 1024 * 1024:

            bins[3] += 1

        else:

            bins[4] += 1

    # =========================================================
    # Content Types
    # =========================================================

    ct_counts = Counter(
        row[3]
        for row in visit
    ).most_common()

    # =========================================================
    # Build Report
    # =========================================================

    L = [

        f"Name: {args.name}",

        f"USC ID: {args.usc_id}",

        (
            f"News site crawled: "
            f"{SITE_DOMAINS[args.site]}"
        ),

        (
            f"Number of threads: "
            f"{args.threads}"
        ),

        "",

        "Fetch Statistics",

        "================",

        (
            f"# fetches attempted: "
            f"{attempted}"
        ),

        (
            f"# fetches succeeded: "
            f"{succeeded}"
        ),

        (
            f"# fetches failed or aborted: "
            f"{failed}"
        ),

        "",

        "Outgoing URLs:",

        "==============",

        (
            f"Total URLs extracted: "
            f"{total_extracted}"
        ),

        (
            f"# unique URLs extracted: "
            f"{unique_total}"
        ),

        (
            f"# unique URLs within News Site: "
            f"{unique_in}"
        ),

        (
            f"# unique URLs outside News Site: "
            f"{unique_out}"
        ),

        "",

        "Status Codes:",

        "=============",
    ]

    L += [
        f"{status_label(code)}: {count}"
        for code, count in status_counts
    ]

    L += [

        "",

        "File Sizes:",

        "===========",

        f"< 1KB: {bins[0]}",

        f"1KB ~ <10KB: {bins[1]}",

        f"10KB ~ <100KB: {bins[2]}",

        f"100KB ~ <1MB: {bins[3]}",

        f">= 1MB: {bins[4]}",

        "",

        "Content Types:",

        "==============",
    ]

    L += [
        f"{content_type}: {count}"
        for content_type, count in ct_counts
    ]

    if args.note:

        L += [

            "",

            f"Note: {args.note}"
        ]

    # =========================================================
    # Write report
    # =========================================================

    out_path = os.path.join(
        d,
        f"CrawlReport_{args.site}.txt"
    )

    with open(
        out_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "\n".join(L)
            + "\n"
        )

    print(
        "\n".join(L)
    )

    print(
        f"\n==> written to {out_path}\n"
    )

    # =========================================================
    # Rubric Checks
    # =========================================================

    count_200 = (
        numeric_statuses.count(200)
    )

    checks = [

        (
            "attempted = succeeded + failed",
            attempted
            == succeeded + failed
        ),

        (
            "unique = within + outside",
            unique_total
            == unique_in + unique_out
        ),

        (
            "200 count == succeeded "
            "(no other 2xx codes)",
            count_200
            == succeeded
        ),

        (
            "file-size total <= succeeded",
            sum(bins)
            <= succeeded
        ),

        (
            "content-type total <= succeeded",
            sum(
                n
                for _, n in ct_counts
            )
            <= succeeded
        ),

        (
            "visit rows within 10% of succeeded",
            (
                succeeded == 0
                or len(visit)
                >= 0.9 * succeeded
            )
        ),

        (
            f"attempted within 2,000 "
            f"of {args.max_pages}",
            attempted
            >= args.max_pages - 2000
        ),
    ]

    print(
        "Rubric checks:"
    )

    for name, ok in checks:

        print(
            f"  "
            f"[{'PASS' if ok else 'FAIL'}] "
            f"{name}"
        )

    print(

        f"\n  (info) urls.csv rows = "
        f"{len(urls)}, "

        f"total extracted = "
        f"{total_extracted}; "

        f"difference = redirect targets / "
        f"seed URL "
        f"({len(urls) - total_extracted})"
    )

    return (
        0
        if all(
            ok
            for _, ok in checks
        )
        else 1
    )


if __name__ == "__main__":

    sys.exit(
        main()
    )