"""
HW1 Task 2: Compare hw1.json (your Yahoo scrape) against Google_Result2.json
and produce hw1.csv with per-query overlap %, Spearman coefficient, and
the overall averages.
"""

import json
import csv
import re


def normalize_url(url):
    """
    Treat these as identical, per the HW1 FAQ:
      - http:// vs https://
      - with vs without leading www.
      - trailing slash vs none
    Do NOT lowercase (the FAQ explicitly says not to).
    """
    u = url.strip()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = u.rstrip("/")
    return u


def find_matches(search_results, google):
    """
    For each query, find which of your search engine's URLs also appear
    in the Google reference list, using normalized comparison, and record
    (google_rank, your_rank) pairs (1-indexed).
    """
    matches = []

    for query in search_results:
        if query not in google:
            # Shouldn't happen if both files use the same query set, but
            # guard against it rather than crashing.
            matches.append([])
            continue

        google_urls = google[query]
        google_norm = [normalize_url(u) for u in google_urls]

        temp = []
        for rank, url in enumerate(search_results[query]):
            url_norm = normalize_url(url)
            if url_norm in google_norm:
                google_rank = google_norm.index(url_norm) + 1
                temp.append([google_rank, rank + 1])

        matches.append(temp)

    return matches


def spearman_coefficient(data):
    overlap_list = []
    overlap_percent_list = []
    spearman_list = []

    sum_overlap = 0
    sum_overlap_percent = 0
    sum_spearman = 0

    for matches in data:
        n = len(matches)

        overlap_list.append(n)
        sum_overlap += n

        # Percent overlap is out of Google's list size (normally 10).
        percent = round(n / 10 * 100.0, 1)
        overlap_percent_list.append(percent)
        sum_overlap_percent += percent

        if n == 0:
            coefficient = 0
        elif n == 1:
            g_rank, y_rank = matches[0]
            coefficient = 1 if g_rank == y_rank else 0
        else:
            d2_sum = sum((g - y) ** 2 for g, y in matches)
            coefficient = 1 - 6 * d2_sum / (n * (n ** 2 - 1))

        spearman_list.append(coefficient)
        sum_spearman += coefficient

    total = len(data)
    avg_overlap = sum_overlap / total
    avg_overlap_percent = sum_overlap_percent / total
    avg_spearman = sum_spearman / total

    return (
        overlap_list,
        overlap_percent_list,
        spearman_list,
        avg_overlap,
        avg_overlap_percent,
        avg_spearman,
    )


def build_summary_text(engine_name, avg_overlap_percent, avg_spearman):
    if avg_overlap_percent >= 50:
        overlap_desc = "a substantial amount of overlap"
    elif avg_overlap_percent >= 20:
        overlap_desc = "a moderate amount of overlap"
    else:
        overlap_desc = "very little overlap"

    if avg_spearman > 0.3:
        rank_desc = (
            "when results do overlap, they also tend to appear in a "
            "similar rank order to Google's, indicating some agreement "
            "in how the two engines prioritize relevant pages"
        )
    elif avg_spearman > -0.3:
        rank_desc = (
            "the ranking of overlapping results shows little consistent "
            "relationship to Google's ordering"
        )
    else:
        rank_desc = (
            "the ranking of overlapping results tends to be inversely "
            "related to Google's ordering, meaning the two engines "
            "largely disagree on how to prioritize the same pages"
        )

    return (
        f"Comparing {engine_name} against Google over all 100 queries in "
        f"the assigned dataset, {engine_name} returned {overlap_desc} with "
        f"Google's results. The average percent overlap was "
        f"{avg_overlap_percent:.1f}% and the average Spearman coefficient "
        f"was {avg_spearman:.4f}. This means that on average, only "
        f"{avg_overlap_percent:.1f}% of {engine_name}'s top-10 results for "
        f"a given query also appeared in Google's top-10 results for that "
        f"same query, and {rank_desc}. Overall, {engine_name} performs "
        f"{'similarly to' if avg_overlap_percent >= 40 and avg_spearman > 0 else 'noticeably differently from'} "
        f"Google for this query set, suggesting the two search engines use "
        f"different ranking algorithms and/or relevance signals when "
        f"selecting and ordering organic results."
    )


def main():
    yahoo_file = "./hw1.json"
    google_file = "./Google_Result2.json"
    output_file = "./hw1.csv"
    summary_file = "./hw1.txt"

    with open(yahoo_file, "r", encoding="utf-8") as f:
        yahoo_result = json.load(f)

    with open(google_file, "r", encoding="utf-8") as f:
        google_result = json.load(f)

    matches = find_matches(yahoo_result, google_result)

    (
        overlap_list,
        overlap_percent_list,
        spearman_list,
        avg_overlap,
        avg_overlap_percent,
        avg_spearman,
    ) = spearman_coefficient(matches)

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Queries", "Number of Overlapping Results",
             "Percent Overlap", "Spearman Coefficient"]
        )
        for i in range(len(overlap_list)):
            writer.writerow(
                [f"Query {i + 1}", overlap_list[i],
                 overlap_percent_list[i], spearman_list[i]]
            )
        writer.writerow(
            ["Averages", avg_overlap, avg_overlap_percent, avg_spearman]
        )

    summary_text = build_summary_text("Yahoo!", avg_overlap_percent, avg_spearman)
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary_text + "\n")

    print("Task 2 completed. Generated:", output_file, "and", summary_file)
    print("Average Percent Overlap:", avg_overlap_percent)
    print("Average Spearman Coefficient:", avg_spearman)


if __name__ == "__main__":
    main()