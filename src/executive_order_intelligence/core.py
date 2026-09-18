"""Core taxonomy and deterministic classification helpers.

This public module is an ENHANCED, SANITIZED DERIVATIVE of the recovered
historical V3 classifier. See docs/PROVENANCE.md for the evidence boundary.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

import pandas as pd

MODEL_NAME = "all-MiniLM-L6-v2"
CLASSIFICATION_VERSION = "EO_NLP_V3_2026_05_PUBLIC"
LOW_CONFIDENCE_THRESHOLD = 0.30
SECONDARY_CLOSE_GAP = 0.04

DOMAIN_DESCRIPTIONS = {
    "DEI / Civil Rights / Merit": (
        "diversity equity inclusion civil rights discrimination equal opportunity "
        "merit affirmative action race sex gender religious freedom"
    ),
    "Government Efficiency / Federal Workforce": (
        "federal workforce civil service employees hiring telework labor relations "
        "government efficiency procurement contracting waste fraud agency reform"
    ),
    "Regulation / Deregulation / Administrative Law": (
        "regulation deregulation rulemaking administrative law compliance permitting "
        "regulatory burden enforcement"
    ),
    "Economy / Finance / Markets": (
        "banking finance financial markets investors retirement bitcoin digital assets "
        "treasury capital markets economic growth"
    ),
    "Immigration / Borders / Foreign Nationals": (
        "immigration visas foreign nationals border asylum refugees citizenship "
        "deportation detention migration"
    ),
    "National Security / Defense / Foreign Policy": (
        "national security defense military foreign policy sanctions intelligence "
        "terrorism cybersecurity arms foreign adversary"
    ),
    "Health / Drugs / Family Policy": (
        "health healthcare drugs opioids fentanyl pharmaceutical medicare medicaid "
        "family policy public health veterans"
    ),
    "Housing / Infrastructure / Transportation": (
        "housing transportation infrastructure railroads roads bridges maritime "
        "broadband airports construction"
    ),
    "Environment / Energy / Natural Resources": (
        "environment energy oil gas coal minerals climate power grid water forests "
        "natural resources conservation"
    ),
    "Law Enforcement / Public Safety / Justice": (
        "law enforcement public safety justice crime criminal prosecution policing "
        "courts prisons trafficking"
    ),
    "Technology / AI / Data / Science": (
        "artificial intelligence machine learning software data centers cybersecurity "
        "quantum science cloud technology"
    ),
    "Education / Sports / Culture": (
        "education schools universities colleges students accreditation sports culture "
        "workforce training"
    ),
    "Trade / Domestic Production / Buy American": (
        "trade tariffs imports exports buy american manufacturing domestic production "
        "supply chain customs"
    ),
    "Administrative / Ceremonial / Government Closure": (
        "administrative ceremonial closure holiday succession revocation rescission "
        "commission council task force"
    ),
}

DEI_TERMS = [
    "dei", "diversity", "equity", "inclusion", "gender ideology",
    "discrimination", "affirmative action", "racial preference", "race",
]
IMMIGRATION_TERMS = [
    "immigration", "immigrant", "visa", "visas", "border", "asylum", "refugee",
    "citizenship", "deportation", "foreign national", "gold card",
]
CONTRACT_TERMS = [
    "federal contracting", "government contracting", "procurement", "acquisition",
    "federal contractor", "government contractor",
]
BUY_AMERICAN_TERMS = [
    "buy american", "made in america", "american-made", "domestic production",
]


def safe_str(value: object) -> str:
    """Return a stripped string while treating pandas missing values as empty."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def clean_text(text: object) -> str:
    """Normalize case/spacing while retaining word, slash, hyphen, and parenthesis characters."""
    normalized = str(text).lower()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"[^\w\s\-/()]", " ", normalized)
    return normalized.strip()


def hash_text(text: object) -> str:
    """Return a compact reproducibility fingerprint."""
    return hashlib.sha256(str(text).encode("utf-8", errors="ignore")).hexdigest()[:16]


def find_keyword_matches(text: object, terms: Iterable[str]) -> list[str]:
    """Return unique terms found in cleaned text, preserving deterministic ordering."""
    haystack = clean_text(text)
    return sorted({term for term in terms if clean_text(term) in haystack})


def priority_rule_classifier(text: object) -> dict[str, object] | None:
    """Apply recovered V2/V3 rule precedence: DEI, immigration, contracting, Buy American."""
    checks = [
        (
            "DEI / Civil Rights / Merit",
            "DEI priority override",
            DEI_TERMS,
            "DEI",
        ),
        (
            "Immigration / Borders / Foreign Nationals",
            "Immigration priority rule",
            IMMIGRATION_TERMS,
            "Immigration",
        ),
        (
            "Government Efficiency / Federal Workforce",
            "Contracting / procurement priority rule",
            CONTRACT_TERMS,
            "Govt Contracts",
        ),
        (
            "Trade / Domestic Production / Buy American",
            "Buy American / domestic production priority rule",
            BUY_AMERICAN_TERMS,
            "Govt Contracts / Domestic Preference",
        ),
    ]
    for domain, rule_name, terms, priority_area in checks:
        matches = find_keyword_matches(text, terms)
        if matches:
            return {
                "domain": domain,
                "rule_name": rule_name,
                "keyword_matches": matches,
                "priority_area": priority_area,
            }
    return None


def classify_subcategory(text: object, domain: str) -> str:
    """Assign an ordered deterministic subcategory within the selected policy domain."""
    t = clean_text(text)

    if domain == "Government Efficiency / Federal Workforce":
        if any(k in t for k in ("contracting", "procurement", "acquisition")):
            return "Federal Contracting / Procurement"
        if any(k in t for k in ("waste", "fraud", "abuse")):
            return "Waste / Fraud / Abuse"
        if any(k in t for k in ("union", "collective bargaining", "labor-management")):
            return "Federal Labor Relations"
        return "Federal Workforce / Operations"

    if domain == "Immigration / Borders / Foreign Nationals":
        if any(k in t for k in ("visa", "visas", "gold card")):
            return "Visas / Entry"
        if "border" in t:
            return "Border Security"
        if any(k in t for k in ("refugee", "asylum")):
            return "Refugees / Asylum"
        return "Immigration Enforcement / Status"

    if domain == "DEI / Civil Rights / Merit":
        if any(k in t for k in ("dei", "diversity", "equity", "inclusion")):
            return "DEI Programs / Policy"
        if any(k in t for k in ("merit", "affirmative action", "preference")):
            return "Merit / Preferential Treatment"
        return "Civil Rights / Equal Opportunity"

    if domain == "Technology / AI / Data / Science":
        if "artificial intelligence" in t or re.search(r"\bai\b", t):
            return "Artificial Intelligence"
        if "cyber" in t:
            return "Cybersecurity"
        if "data center" in t:
            return "Data Centers"
        if "quantum" in t or "research" in t or "science" in t:
            return "Science / Research"
        return "Technology / Data"

    if domain == "Trade / Domestic Production / Buy American":
        if "buy american" in t or "american-made" in t:
            return "Buy American"
        if "supply chain" in t:
            return "Supply Chain"
        if any(k in t for k in ("tariff", "trade", "import", "export")):
            return "Trade / Tariffs"
        return "Domestic Production / Manufacturing"

    if domain == "Environment / Energy / Natural Resources":
        if any(k in t for k in ("energy", "grid", "electricity", "power")):
            return "Energy / Power Grid"
        if any(k in t for k in ("oil", "gas", "coal", "mineral")):
            return "Domestic Energy / Minerals"
        if any(k in t for k in ("climate", "environmental")):
            return "Environmental / Climate Policy"
        return "Natural Resource Management"

    if domain == "National Security / Defense / Foreign Policy":
        if "sanction" in t:
            return "Sanctions"
        if any(k in t for k in ("military", "defense", "arms")):
            return "Defense / Military"
        if "cyber" in t:
            return "Cyber / National Security"
        return "Foreign Policy / National Security"

    if domain == "Health / Drugs / Family Policy":
        if any(k in t for k in ("fentanyl", "opioid", "drug")):
            return "Drugs / Addiction"
        if any(k in t for k in ("pharmaceutical", "medicine", "drug price")):
            return "Pharmaceutical / Drug Pricing"
        return "Health / Family Policy"

    if domain == "Housing / Infrastructure / Transportation":
        if any(k in t for k in ("rail", "railroad")):
            return "Rail"
        if any(k in t for k in ("maritime", "port")):
            return "Maritime / Ports"
        if "broadband" in t:
            return "Broadband Infrastructure"
        return "Infrastructure / Transportation"

    if domain == "Law Enforcement / Public Safety / Justice":
        if "election" in t:
            return "Election Integrity"
        if "trafficking" in t:
            return "Human Trafficking"
        return "Crime / Criminal Justice"

    if domain == "Education / Sports / Culture":
        if any(k in t for k in ("sports", "athletics")):
            return "Sports / College Athletics"
        if any(k in t for k in ("school", "education", "student", "university", "college")):
            return "Education Policy"
        return "Education / Culture"

    if domain == "Economy / Finance / Markets":
        if any(k in t for k in ("bitcoin", "crypto", "digital asset")):
            return "Digital Assets"
        if any(k in t for k in ("bank", "banking")):
            return "Banking"
        if any(k in t for k in ("retirement", "401k")):
            return "Retirement / Investment"
        return "Economy / Markets"

    if domain == "Regulation / Deregulation / Administrative Law":
        if "deregulat" in t or "regulatory relief" in t:
            return "Deregulation / Regulatory Relief"
        if "permit" in t:
            return "Permitting"
        return "Rulemaking / Administrative Law"

    if domain == "Administrative / Ceremonial / Government Closure":
        if any(k in t for k in ("closing", "closure", "holiday")):
            return "Federal Holiday / Closure"
        if any(k in t for k in ("revocation", "rescission", "revoke", "rescind")):
            return "Revocation / Rescission"
        if any(k in t for k in ("board", "council", "commission", "task force")):
            return "Boards / Councils / Commissions"
        return "Administrative / Ceremonial"

    return "General"
