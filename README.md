# Local SEO Citation Directory Discovery Engine

A Python-based automation tool for discovering business directories and citation sources for Local SEO workflows.

This project collects potential business listing platforms through search APIs and validates which domains look like real submission directories. The repository only contains the discovery engine. Generated CSV databases, API keys, and other private data assets are intentionally excluded from version control.

## Features

- Automated directory discovery using search queries
- Domain normalization and duplicate removal
- Validation engine for directory detection
- Incremental local database growth
- GitHub-safe defaults for ignoring data assets and secrets

## Project Structure

```text
citation-directory-discovery-engine/
collector.py
validator.py
queries.txt
requirements.txt
README.md
.gitignore
```

## Workflow

```text
collector.py
↓
validator.py
↓
directories_valid.csv (local database)
```

The CSV database grows automatically while avoiding duplicates.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python collector.py
python validator.py
```

## Data Safety

The following files are intentionally excluded from the public repository:

- `directories_valid.csv`
- `directories_raw.csv`
- `.env`
- `api_keys.txt`

## Disclaimer

This repository contains only the discovery engine. The collected directory database is intentionally excluded from GitHub.
