from __future__ import annotations

from datetime import datetime
from pathlib import Path
from time import sleep
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "directories_raw.csv"
OUTPUT_FILE = BASE_DIR / "directories_valid.csv"
BACKUP_FILE = BASE_DIR / "directories_valid.backup.csv"
SNAPSHOT_DIR = BASE_DIR / "snapshots"
TIMEOUT = 10
REQUEST_DELAY_SECONDS = 0.5
SAVE_EVERY = 25
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
CSV_COLUMNS = [
    "Directory Name",
    "Website URL",
    "Submission URL",
    "Country",
    "Niche",
    "Global",
    "Captcha",
    "Email Verification",
    "Automation Ready",
    "Notes",
]
CONTENT_KEYWORDS = [
    "add business",
    "submit listing",
    "business directory",
    "add company",
    "submit business",
]
SUBMISSION_HINTS = [
    "add-business",
    "add business",
    "submit-business",
    "submit business",
    "submit-listing",
    "submit listing",
    "create-listing",
    "create listing",
    "add-company",
    "add company",
    "list-your-business",
    "list your business",
    "get-listed",
    "get listed",
    "claim-business",
    "claim business",
    "register-business",
    "register business",
]
CAPTCHA_HINTS = ["captcha", "recaptcha", "hcaptcha", "g-recaptcha"]
EMAIL_HINTS = [
    "verify your email",
    "email verification",
    "confirm your email",
    "activation email",
]
AUTOMATION_BLOCKERS = [
    "captcha",
    "recaptcha",
    "hcaptcha",
    "cloudflare",
    "access denied",
]


def build_session() -> requests.Session:
    retry = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
    )
    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.headers.update(HEADERS)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def normalize_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    url = value.strip()
    if not url:
        return None

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    return url


def normalize_domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def load_existing_valid_dataframe() -> pd.DataFrame:
    if not OUTPUT_FILE.exists():
        return pd.DataFrame(columns=CSV_COLUMNS)

    dataframe = pd.read_csv(OUTPUT_FILE)
    for column in CSV_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = ""

    if "Website URL" not in dataframe.columns:
        return pd.DataFrame(columns=CSV_COLUMNS)

    dataframe["Website URL"] = dataframe["Website URL"].apply(normalize_url)
    dataframe.dropna(subset=["Website URL"], inplace=True)
    dataframe["Normalized Domain"] = dataframe["Website URL"].apply(normalize_domain)
    dataframe.drop_duplicates(subset=["Website URL"], inplace=True)
    dataframe.drop_duplicates(subset=["Normalized Domain"], inplace=True)
    return dataframe


def load_raw_dataframe() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        return pd.DataFrame(columns=CSV_COLUMNS)

    dataframe = pd.read_csv(INPUT_FILE)
    if "Website URL" not in dataframe.columns:
        return pd.DataFrame(columns=CSV_COLUMNS)

    for column in CSV_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = ""

    dataframe["Website URL"] = dataframe["Website URL"].apply(normalize_url)
    dataframe.dropna(subset=["Website URL"], inplace=True)
    dataframe.drop_duplicates(subset=["Website URL"], inplace=True)
    return dataframe[CSV_COLUMNS]


def find_submission_url(base_url: str, soup: BeautifulSoup) -> str:
    for link in soup.select("a[href], form[action]"):
        href = link.get("href") or link.get("action")
        if not isinstance(href, str):
            continue

        text = " ".join(link.stripped_strings).lower()
        target = href.lower()

        if any(hint in text or hint in target for hint in SUBMISSION_HINTS):
            return urljoin(base_url, href)

    return ""


def detect_captcha(text: str) -> str:
    return "Yes" if any(hint in text for hint in CAPTCHA_HINTS) else "No"


def detect_email_verification(text: str) -> str:
    return "Yes" if any(hint in text for hint in EMAIL_HINTS) else "Unknown"


def detect_automation_ready(page_text: str, submission_url: str) -> str:
    if not submission_url:
        return "No"
    if any(blocker in page_text for blocker in AUTOMATION_BLOCKERS):
        return "No"
    return "Yes"


def build_notes(page_text: str, matched_keywords: list[str], submission_url: str) -> str:
    notes: list[str] = []
    if matched_keywords:
        notes.append("keywords=" + ", ".join(matched_keywords))
    if submission_url:
        notes.append("submission page detected")
    if "claim" in page_text:
        notes.append("claim flow possible")
    if "free listing" in page_text:
        notes.append("free listing mention")
    return " | ".join(notes)


def validate_directory(session: requests.Session, row: pd.Series) -> dict[str, str] | None:
    website_url = row["Website URL"]

    try:
        response = session.get(website_url, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"Skipped URL: {website_url} -> {error}")
        return None

    sleep(REQUEST_DELAY_SECONDS)
    page_text = response.text.lower()
    matched_keywords = [keyword for keyword in CONTENT_KEYWORDS if keyword in page_text]
    if not matched_keywords:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    submission_url = find_submission_url(response.url, soup)
    directory_name = (
        row["Directory Name"]
        if isinstance(row["Directory Name"], str) and row["Directory Name"].strip()
        else normalize_domain(response.url)
    )

    return {
        "Directory Name": directory_name,
        "Website URL": response.url,
        "Submission URL": submission_url,
        "Country": row.get("Country", ""),
        "Niche": row.get("Niche", ""),
        "Global": row.get("Global", ""),
        "Captcha": detect_captcha(page_text),
        "Email Verification": detect_email_verification(page_text),
        "Automation Ready": detect_automation_ready(page_text, submission_url),
        "Notes": build_notes(page_text, matched_keywords, submission_url),
    }


def save_progress(rows: list[dict[str, str]]) -> None:
    if OUTPUT_FILE.exists():
        BACKUP_FILE.write_text(OUTPUT_FILE.read_text(encoding="utf-8"), encoding="utf-8")

    dataframe = pd.DataFrame(rows, columns=CSV_COLUMNS)
    if not dataframe.empty:
        dataframe["Normalized Domain"] = dataframe["Website URL"].apply(normalize_domain)
        dataframe.drop_duplicates(subset=["Website URL"], inplace=True)
        dataframe.drop_duplicates(subset=["Normalized Domain"], inplace=True)
        dataframe.sort_values(by=["Website URL"], inplace=True)
        dataframe.drop(columns=["Normalized Domain"], inplace=True)
    dataframe.to_csv(OUTPUT_FILE, index=False)

    SNAPSHOT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_path = SNAPSHOT_DIR / f"directories_valid_{timestamp}.csv"
    dataframe.to_csv(snapshot_path, index=False)


def main() -> None:
    raw_dataframe = load_raw_dataframe()
    total_urls = len(raw_dataframe)
    existing_valid_dataframe = load_existing_valid_dataframe()
    existing_domains = set(existing_valid_dataframe["Normalized Domain"]) if "Normalized Domain" in existing_valid_dataframe.columns else set()

    if raw_dataframe.empty:
        if not existing_valid_dataframe.empty:
            print("No raw URLs found to validate.")
            print(f"Kept existing validation database unchanged: {OUTPUT_FILE}")
            return

        pd.DataFrame(columns=CSV_COLUMNS).to_csv(OUTPUT_FILE, index=False)
        print("No raw URLs found to validate.")
        print(f"Saved empty validation output to: {OUTPUT_FILE}")
        return

    valid_rows: list[dict[str, str]] = []
    checked = 0

    with build_session() as session:
        for _, row in raw_dataframe.iterrows():
            checked += 1
            print(f"Checking {checked}/{total_urls}: {row['Website URL']}")
            validated_row = validate_directory(session, row)
            if validated_row is not None:
                normalized_domain = normalize_domain(validated_row["Website URL"])
                if normalized_domain in existing_domains:
                    print(f"Skipped existing domain: {validated_row['Website URL']}")
                else:
                    existing_domains.add(normalized_domain)
                    valid_rows.append(validated_row)
                    print(f"Valid match found: {validated_row['Website URL']}")

            if checked % SAVE_EVERY == 0:
                combined_rows = existing_valid_dataframe[CSV_COLUMNS].to_dict("records") + valid_rows
                save_progress(combined_rows)
                print(f"Progress saved at {checked}/{total_urls}. Current new valid count: {len(valid_rows)}")

    combined_rows = existing_valid_dataframe[CSV_COLUMNS].to_dict("records") + valid_rows
    save_progress(combined_rows)
    print(f"Validation complete. New valid directories added: {len(valid_rows)}")
    print(f"Validation output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
