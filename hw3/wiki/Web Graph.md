---
title: "Web Graph"
type: "concept"
category: "Network Theory"
language: "en"
aliases:
  - "Linkage"
  - "In-degree"
  - "Out-degree"
tags:
  - "wiki/concept"
  - "network-theory"
sources:
  - "[[Sources/CharacterizingtheWeb|CharacterizingtheWeb.pdf]]"
updated: "2026-11-03"
---

# Web Graph

> [!abstract] Summary
> A mathematical representation of the Web as a collection of nodes (pages) and edges (links) to analyze structure and connectivity.

## Structural Modeling
The web is modeled as a massive graph where individual web pages serve as nodes and the hyperlinks between them represent directed edges. This model is critical for understanding how information flows across the internet. Analysis of the Web Graph reveals specific topological properties; notably, the distribution of in-degree (incoming links) and out-degree (outgoing links) follows a power law distribution. This implies that while most pages have very few connections, a small subset of pages (hubs) possesses an extremely high number of links.

## Importance in Retrieval
Graph analysis provides deeper insights into the reach and influence of websites. It is the backbone for many ranking algorithms that determine content importance. Furthermore, the graph structure dictates how a [[Web Crawler]] navigates the web; crawlers follow these edges to discover new content, essentially performing a traversal of the global graph. Understanding the structure of the web is thus essential for both mapping the internet and calculating the authority of individual pages.

## Related Concepts
* [[Web Crawler]]: Utilizes the graph structure to navigate from page to page.
* [[Web Search Indexing]]: Often leverages link-based graph analysis to determine the relevance of indexed documents.

## Sources & Provenance
- [[Sources/CharacterizingtheWeb|CharacterizingtheWeb.pdf]]
