---
name: strict-scraper-fidelity
description: Enforces 100% strict live website fidelity for scraped lesson reports. Prevents hallucinating or inserting mock fallback data.
---

# Strict Live Scraper Fidelity Guidelines

## Core Principles

1. **100% Live Scraped Content**: Every line of lesson text, reading assignment, homework task, spelling word, quiz, test, and school event in generated weekly reports MUST be strictly derived ONLY from live scraped content from the official Google Sites network.
2. **Zero Mock/Fallback Hallucination**: NEVER introduce mock, synthetic, or static template fallback tasks (such as generic "Module 2", "Cause and effect essay", "Edclub Python syntax") when a scraped section or subpage is empty.
3. **Empty Handling**: If a teacher's page or section has no announcements or assignments listed for the active week, output: `"No explicit homework listed for this week"` instead of inventing placeholder assignments.
4. **Dynamic Weekly Subpage Discovery**: Teacher URLs change every week as new weeks progress (e.g. `week-8-sep-28-oct-2`, `week-of-092826`). Scrape from the subject's grade-level base URL, inspect available subpage links, select the active week link dynamically, and scrape that page.
5. **Exact Teacher Terminology**: Preserve exact phrasing, dates, page numbers, and surah/ayah references as written by the teacher on the Google Site.
