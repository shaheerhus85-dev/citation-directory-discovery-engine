# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from time import sleep
from typing import Any
from urllib.parse import urlparse

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent
QUERIES_FILE = BASE_DIR / "queries.txt"
OUTPUT_FILE = BASE_DIR / "directories_raw.csv"
STATE_FILE = BASE_DIR / "collector_state.json"
TAVILY_ENDPOINT = "https://api.tavily.com/search"
TIMEOUT = 20
MAX_RESULTS_PER_QUERY = 10
CSV_COLUMNS = ["Directory Name", "Website URL"]
BLOCKED_HOSTS = {
    "google.com",
    "youtube.com",
    "facebook.com",
    "linkedin.com",
    "wikipedia.org",
    "duckduckgo.com",
}


def load_queries() -> list[str]:
    if not QUERIES_FILE.exists():
        return []
    return [line.strip().strip('"') for line in QUERIES_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]


def compute_query_signature(queries: list[str]) -> str:
    joined = "\n".join(queries).encode("utf-8")
    return hashlib.sha1(joined).hexdigest()


def load_query_state(signature: str) -> int:
    if not STATE_FILE.exists():
        return 0

    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0

    saved_signature = data.get("signature")
    next_query_index = data.get("next_query_index", 0)
    if saved_signature != signature:
        return 0
    if not isinstance(next_query_index, int) or next_query_index < 0:
        return 0
    return next_query_index


def save_query_state(signature: str, next_query_index: int) -> None:
    payload = {
        "signature": signature,
        "next_query_index": next_query_index,
    }
    STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_api_key() -> str:
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if api_key:
        return api_key

    env_path = BASE_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("TAVILY_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")

    raise RuntimeError("TAVILY_API_KEY not found. Set it in environment or .env")


def root_domain(hostname: str) -> str:
    parts = hostname.lower().split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return hostname.lower()


def normalize_result_url(raw_url: str) -> str | None:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    domain = root_domain(parsed.netloc.removeprefix("www."))
    if domain in BLOCKED_HOSTS:
        return None

    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def build_record(url: str) -> dict[str, str]:
    hostname = urlparse(url).netloc.removeprefix("www.")
    return {
        "Directory Name": hostname,
        "Website URL": url,
    }


def fetch_query_results(session: requests.Session, api_key: str, query: str) -> list[str]:
    payload: dict[str, object] = {
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": MAX_RESULTS_PER_QUERY,
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False,
    }
    response = session.post(TAVILY_ENDPOINT, json=payload, timeout=TIMEOUT)
    response.raise_for_status()

    data: Any = response.json()
    if not isinstance(data, dict):
        return []

    raw_results = data.get("results")
    if not isinstance(raw_results, list):
        return []

    urls: list[str] = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue

        raw_url = item.get("url")
        if not isinstance(raw_url, str):
            continue

        clean_url = normalize_result_url(raw_url)
        if clean_url is None:
            continue

        urls.append(clean_url)

    return urls


def is_rate_limit_error(error: requests.RequestException) -> bool:
    response = getattr(error, "response", None)
    return response is not None and response.status_code == 432


def main() -> int:
    api_key = load_api_key()
    queries = load_queries()
    signature = compute_query_signature(queries)
    start_index = load_query_state(signature)
    results: list[dict[str, str]] = []
    seen_domains: set[str] = set()
    rate_limited = False

    if start_index > 0:
        print(f"Resuming query pack from query {start_index + 1} of {len(queries)}")

    with requests.Session() as session:
        for query_index in range(start_index, len(queries)):
            query = queries[query_index]
            query_new_domains = 0

            try:
                query_urls = fetch_query_results(session, api_key, query)
            except requests.RequestException as error:
                if is_rate_limit_error(error):
                    print("Tavily rate limit or usage cap reached.")
                    print(f"Stopped on query: {query}")
                    print("Save current results, wait for quota reset or reduce query volume, then run again.")
                    rate_limited = True
                    save_query_state(signature, query_index)
                    break
                print(f"Skipped query: {query} -> {error}")
                continue

            for query_url in query_urls:
                domain = root_domain(urlparse(query_url).netloc.removeprefix("www."))
                if domain in seen_domains:
                    continue

                seen_domains.add(domain)
                results.append(build_record(query_url))
                query_new_domains += 1

            print(f"Domains collected for query '{query}': {query_new_domains}")
            sleep(1)

    dataframe = pd.DataFrame(results, columns=CSV_COLUMNS)
    if dataframe.empty:
        dataframe = pd.DataFrame(columns=CSV_COLUMNS)
    else:
        dataframe.drop_duplicates(subset=["Website URL"], inplace=True)
        dataframe.sort_values(by=["Website URL"], inplace=True)

    dataframe.to_csv(OUTPUT_FILE, index=False)
    print(f"Total domains collected: {len(dataframe)}")
    print(f"Saved raw output to: {OUTPUT_FILE}")
    if not rate_limited:
        save_query_state(signature, 0)
    return 2 if rate_limited else 0


if __name__ == "__main__":
    sys.exit(main())
