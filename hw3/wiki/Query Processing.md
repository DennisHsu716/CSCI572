---
title: "Query Processing"
type: "concept"
category: "Search Architecture"
language: "en"
aliases:
  - "Query Reformulation"
tags:
  - "wiki/concept"
  - "search-architecture"
sources:
  - "[[Sources/SearchEngineBasics|SearchEngineBasics.pdf]]"
updated: "2026-11-03"
---

# Query Processing

> [!abstract] Summary
> The process of analyzing and interpreting user search inputs to retrieve and rank relevant documents, involving both front-end normalization and back-end matching (p. 20).

## Functional Pipeline
Query processing acts as the bridge between raw user input and the retrieved search results. The front-end stage is responsible for normalizing the input, which includes tasks like word stemming, handling capitalization, and Boolean optimization (p. 20).

Once normalized, the system moves to semantic analysis. This phase determines the underlying [[User Information Needs]] by filtering out common stop words and performing entity extraction to identify specific types such as people, geographic locations, or stock market symbols (p. 24). 

## Contextual Integration
Advanced engines incorporate external context to refine retrieval, such as:
- **Geographic Data**: Localizing results based on the user's current area (p. 24).
- **Query History**: Leveraging past interactions to personalize results (p. 24).
- **Holistic Results**: Modern systems aggregate diverse content types, including maps, facts, and multimedia, to provide a comprehensive answer rather than a simple list of links (p. 26-28).

## Related Concepts
* [[Inverted Index]]: The data structure queried during the matching process.
* [[User Information Needs]]: The foundational intent analysis that guides query interpretation.

## Sources & Provenance
- [[Sources/SearchEngineBasics|SearchEngineBasics.pdf]]
