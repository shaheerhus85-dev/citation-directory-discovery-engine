# Local SEO Citation Directory Discovery Engine

A Python automation engine for discovering **business directories and citation sources** used in Local SEO campaigns.

This project automatically discovers potential business listing platforms using structured search queries and validates which domains appear to be real submission directories.

The repository contains only the **discovery engine**. Generated CSV databases, API keys, and other private data assets are intentionally excluded from version control.

---

# Key Features

- Automated discovery of business directories using structured search queries
- Domain normalization and duplicate removal
- Validation engine for detecting real directory platforms
- Incremental growth of a local directory database
- Query rotation strategy for continuous discovery
- GitHub-safe defaults that ignore private data and API keys

---

# Project Structure


citation-directory-discovery-engine/

collector.py # Discovers potential directory domains using search queries
validator.py # Validates domains and appends only unique directory sites
queries.txt # Query packs used for directory discovery
requirements.txt # Python dependencies
README.md # Project documentation
.gitignore # Prevents sensitive files and datasets from being uploaded


---

# Workflow

The system works as a two-stage discovery pipeline.


collector.py
↓
validator.py
↓
directories_valid.csv (local database)


### collector.py

- Sends structured search queries
- Extracts potential directory domains from search results
- Stores raw discovery data

### validator.py

- Filters domains that resemble directory platforms
- Normalizes domains
- Removes duplicate domains
- Appends only **new unique directory sites** to the master CSV database

Over multiple runs the system builds a growing database of business directories.

---

# Installation

Clone the repository:


git clone https://github.com/shaheerhuss85-dev/citation-directory-discovery-engine.git

cd citation-directory-discovery-engine


Install dependencies:


pip install -r requirements.txt


---

# Usage

Run the discovery engine:


python collector.py


Then validate discovered domains:


python validator.py


Over time the system builds a continuously expanding citation directory database.

---

# Data Safety

The following files are intentionally **excluded from the public repository**:

- directories_valid.csv
- directories_raw.csv
- .env
- api_keys.txt

These files contain locally generated datasets or API credentials and are ignored using `.gitignore`.

This ensures that private data assets remain local and are never uploaded to GitHub.

---

# Use Cases

This tool can be used for:

- Local SEO research
- Building citation source databases
- SEO automation tools
- Data collection pipelines
- Internal SEO agency workflows

---

# Disclaimer

This repository contains only the **discovery engine**.

The collected citation directory database is intentionally kept private and is not distributed with the project.

---

# License

This project is released for educational and research purposes.
