---
title: "Web Crawler"
type: "concept"
category: "Data Acquisition"
language: "en"
aliases:
  - "Spider"
  - "Robot"
tags:
  - "wiki/concept"
  - "data-acquisition"
sources:
  - "[[Sources/SearchEngineBasics|SearchEngineBasics.pdf]]"
updated: "2026-11-03"
---

# Web Crawler

> [!abstract] Summary
> A software component that recursively fetches web pages, parses their content to extract new URLs, and builds the corpus for the search [[Inverted Index|index]] (p. 20).

## Core Definition
A web crawler is the primary mechanism for building the search corpus required for [[Web Search Indexing]] (p. 20). Often referred to as a spider or robot, these systems systematically browse the internet to identify, download, and catalog content. Early iterations, such as the World Wide Web Wanderer, were critical tools for researchers to measure the rapid growth of the early internet (p. 5).

## Technical Details & Mechanisms
The operational lifecycle of a crawler is iterative and resource-intensive. The process functions as follows:
1. **Seed URL Fetching**: The crawler begins with a defined list of known URLs (p. 20).
2. **Parsing**: The crawler fetches the HTML content of the target URL and parses the page to identify new links (p. 20).
3. **Queue Management**: Discovered URLs are added to a crawl queue to be processed in subsequent cycles (p. 20).

Because modern crawlers are significantly resource-intensive, many website administrators now implement filtering mechanisms. Consequently, some sites explicitly block smaller crawlers, allowing access only to major engines like Google and Bing to manage server load (p. 31).

## Sources & Provenance
- [[Sources/SearchEngineBasics|SearchEngineBasics.pdf]]
