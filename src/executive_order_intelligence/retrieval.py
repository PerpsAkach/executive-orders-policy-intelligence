"""Optional public-document retrieval helpers.

This module mirrors the recovered V3 retrieval architecture without private
paths or work-specific configuration. Network use is explicit and isolated.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

MAX_FULL_TEXT_CHARS = 45_000
REQUEST_TIMEOUT_SECONDS = 25
USER_AGENT = "Mozilla/5.0 ExecutiveOrderPolicyIntelligence/0.1"


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def load_cache(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_cache(cache: dict[str, dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def extract_html_body(html: str) -> str:
    """Extract useful document text while suppressing common page chrome."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    chunks: list[str] = []
    for selector in (
        "#fulltext_content_area",
        "#document",
        "#main-content",
        "article",
        "main",
        ".document-content",
    ):
        for item in soup.select(selector):
            text = normalize_space(item.get_text(" "))
            if len(text) >= 500:
                chunks.append(text)

    if not chunks:
        chunks = [
            normalize_space(item.get_text(" "))
            for item in soup.find_all(["p", "section"])
            if len(normalize_space(item.get_text(" "))) >= 80
        ]

    return normalize_space(" ".join(chunks))[:MAX_FULL_TEXT_CHARS]


def fetch_html_text(url: str) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return extract_html_body(response.text)


def fetch_pdf_text(url: str) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    reader = PdfReader(BytesIO(response.content))
    pages: list[str] = []
    for page in reader.pages[:30]:
        text = page.extract_text() or ""
        if text:
            pages.append(text)
    return normalize_space(" ".join(pages))[:MAX_FULL_TEXT_CHARS]


def fetch_with_cache(
    url: str,
    *,
    cache: dict[str, dict[str, str]],
) -> tuple[str, str]:
    """Retrieve one URL, reusing historical-style URL-keyed cache entries."""
    if url in cache:
        entry = cache[url]
        return entry.get("text", ""), entry.get("status", "Cached")

    try:
        if url.lower().split("?", 1)[0].endswith(".pdf"):
            text = fetch_pdf_text(url)
            status = "PDF Full Text" if text else "PDF Text Empty"
        else:
            text = fetch_html_text(url)
            status = "HTML Full Text" if len(text) >= 1500 else "HTML Limited Text"
    except requests.RequestException as exc:
        text = ""
        status = f"URL Extraction Failed: {str(exc)[:120]}"

    cache[url] = {
        "status": status,
        "text": text,
        "retrieved_at": datetime.now().isoformat(timespec="seconds"),
    }
    return text, status
