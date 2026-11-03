---
title: "Inverted Index"
type: "concept"
category: "Data Structures"
language: "en"
aliases:
  - "Index"
tags:
  - "wiki/concept"
  - "data-structures"
sources:
  - "[[Sources/SearchEngineBasics|SearchEngineBasics.pdf]]"
updated: "2026-11-03"
---

# Inverted Index

> [!abstract] Summary
> A core data structure created by the indexer that maps words or tokens to the documents in which they appear, allowing for efficient search retrieval (p. 20).

## Core Definition
The inverted index is the primary output of the [[Web Search Indexing|indexing]] process within the [[Web Technology Stack]] (p. 20). By mapping content tokens to their respective document locations, it enables engines to move beyond simple linear scans, allowing for nearly instantaneous results even when querying massive datasets.

## Technical Capabilities
Modern indices are highly complex structures that support sophisticated linguistic and retrieval features, including:
* **Linguistic Support**: Handling of [[Universal Character Encoding|Unicode]], word stemming, and case normalization (p. 20).
* **Search Precision**: Support for phrase searching and Boolean logic (p. 20).

Historical growth in the search industry was defined by the capacity to scale these structures. Companies like AltaVista and Inktomi gained early dominance specifically through their ability to manage and query increasingly massive indices (p. 7, p. 12). Today, maintaining a competitive index requires such immense computational power and infrastructure that the market has seen significant consolidation, as smaller providers struggle to match the resources required to maintain a comprehensive and up-to-date index (p. 31).

## Related Concepts
* [[Web Crawler]]: The component responsible for gathering the raw data that populates the inverted index.

## Sources & Provenance
- [[Sources/SearchEngineBasics|SearchEngineBasics.pdf]]
