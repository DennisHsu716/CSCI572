---
title: "Web Archiving"
type: "concept"
category: "Digital Preservation"
language: "en"
aliases:
  - "Wayback Machine"
  - "Internet Archive"
tags:
  - "wiki/concept"
  - "digital-preservation"
sources:
  - "[[Sources/CharacterizingtheWeb|CharacterizingtheWeb.pdf]]"
updated: "2026-11-03"
---

# Web Archiving

> [!abstract] Summary
> The practice of periodically capturing and storing snapshots of the World Wide Web to ensure long-term access to historical digital content.

## Crawling and Storage Architecture
Web Archiving requires massive, scalable infrastructure to preserve the evolving state of the internet. The Internet Archive, a primary entity in this field, conducts broad crawls every two months. These operations begin at specific seed sites and utilize a recursive algorithm that traverses internal and external links to capture snapshots of reachable content. The framework frequently employed for these operations is [[Web Technology Stack|Apache]] Nutch. Given the velocity of web content, the archival database size is substantial, reported at approximately 4.5 petabytes, experiencing rapid monthly growth. 

## Scaling Challenges
Archiving a significant portion of the web involves managing storage at the scale of [[Data Storage Metrics]]. For example, archiving one trillion pages, assuming an average size of 100KB per page, necessitates approximately 100 Petabytes of raw storage. As the [[Web Graph|web graph]] continues to grow, archival organizations must balance the frequency of captures with the underlying costs of digital storage, which have fortunately trended downward over time.

## Related Concepts
* [[Data Storage Metrics]]: Provides the standardized units required to measure the massive storage capacity needed for archival repositories.
* [[Web Crawler]]: The foundational tool used by archiving services to traverse links and collect data snapshots.

## Sources & Provenance
- [[Sources/CharacterizingtheWeb|CharacterizingtheWeb.pdf]]
