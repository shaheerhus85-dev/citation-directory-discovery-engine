# Local SEO Citation Directory Discovery Engine

A Python-based automation tool designed to discover **business directories and citation sources** for Local SEO workflows.

This project automates the discovery of potential business listing platforms using search APIs and validates which domains are likely to be real submission directories.

The repository contains only the **discovery engine**. Generated CSV databases, API keys, and other private data assets are intentionally excluded from version control.

---

## Key Features

- Automated discovery of business directories using structured search queries
- Domain normalization and duplicate removal
- Validation engine for detecting real directory platforms
- Incremental growth of a local directory database
- Query rotation strategy for continuous discovery
- GitHub-safe defaults that ignore private data and API keys

---

## Project Structure

```text
citation-directory-discovery-engine/

collector.py        # Discovers potential directory domains using search queries
validator.py        # Validates domains and appends only unique directory sites
queries.txt         # Query packs used for directory discovery
requirements.txt    # Python dependencies
README.md           # Project documentation
.gitignore          # Prevents sensitive files and datasets from being uploaded
