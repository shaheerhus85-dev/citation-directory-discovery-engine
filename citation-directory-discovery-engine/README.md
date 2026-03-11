# Local SEO Citation Directory Discovery Engine

A Python-based automation tool for discovering business directories and citation sources for Local SEO workflows.

This project collects potential business listing platforms through search APIs and validates which domains look like real submission directories. The repository only contains the discovery engine. Generated CSV databases, API keys, and other private data assets are intentionally excluded from version control.

## Features

- Automated directory discovery using search queries
- Query rotation through editable query packs
- Domain normalization and duplicate removal
- Validation engine for directory detection
- Incremental local database growth
- GitHub-safe defaults for ignoring data assets and secrets

## Project Structure

```text
citation-directory-discovery-engine/
├── collector.py
├── validator.py
├── queries.txt
├── requirements.txt
├── README.md
└── .gitignore
```

## Workflow

```text
collector.py
  ↓
validator.py
  ↓
directories_valid.csv (local database, gitignored)
```

The CSV database grows locally while avoiding duplicate domains.

## Requirements

- Python 3.11+
- Tavily API key stored in `TAVILY_API_KEY` or a local `.env` file

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the collector:

```bash
python collector.py
```

Then validate discovered domains:

```bash
python validator.py
```

## Data Safety

These files are excluded from the public repository:

- `directories_valid.csv`
- `directories_raw.csv`
- `*.csv`
- `.env`
- `api_keys.txt`

## Disclaimer

This repository ships only the discovery engine. Collected directory databases and API credentials stay local and should not be committed to GitHub.
