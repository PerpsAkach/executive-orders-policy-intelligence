"""Portable NLP classification pipeline.

The historical V3 source was recovered separately. This module is an ENHANCED
public wrapper designed for reproducibility and safe publication.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .core import (
    CLASSIFICATION_VERSION,
    DOMAIN_DESCRIPTIONS,
    LOW_CONFIDENCE_THRESHOLD,
    MODEL_NAME,
    SECONDARY_CLOSE_GAP,
    classify_subcategory,
    clean_text,
    hash_text,
    priority_rule_classifier,
    safe_str,
)

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:  # pragma: no cover - import error is surfaced at runtime
    SentenceTransformer = None
    util = None


def _text_columns(columns: list[str] | pd.Index) -> list[str]:
    candidates = [
        "Title",
        "title",
        "Summary",
        "summary",
        "abstract",
        "Abstract",
        "description",
        "Description",
    ]
    return [c for c in candidates if c in columns]


def _url_columns(columns: list[str] | pd.Index) -> list[str]:
    candidates = ["html_url", "pdf_url", "URL", "url", "Html_URL", "PDF_URL"]
    return [c for c in candidates if c in columns]


def source_quality(status: str, text_length: int) -> str:
    """Recovered V3 source-quality heuristic."""
    has_full_text = "full text" in status.lower() or "cached" in status.lower()
    if has_full_text and text_length >= 12000:
        return "Strong - Full Text"
    if has_full_text and text_length >= 3000:
        return "Moderate - Full/Limited Text"
    if text_length >= 1000:
        return "Moderate - Excel Text"
    return "Weak - Short Text"


def classify_affected_sector(text: str, domain: str, subcategory: str) -> str:
    t = f" {clean_text(text)} "
    if any(k in t for k in (" procurement ", " contracting ", " contractor ", " acquisition ")):
        return "Federal Contractors / Grant Recipients"
    if domain == "Government Efficiency / Federal Workforce":
        return "Federal Workforce"
    if domain == "Immigration / Borders / Foreign Nationals":
        return "Immigrants / Foreign Nationals"
    if domain == "Education / Sports / Culture":
        return "Education Sector"
    if domain == "National Security / Defense / Foreign Policy":
        return "Defense / National Security"
    if domain == "Health / Drugs / Family Policy":
        return "Health Sector"
    if domain == "Economy / Finance / Markets":
        return "Financial Sector"
    if domain == "Housing / Infrastructure / Transportation":
        return "Infrastructure / Transportation Sector"
    if domain == "Environment / Energy / Natural Resources":
        return "Energy / Environment Sector"
    if domain == "Technology / AI / Data / Science":
        return "Technology Sector"
    if domain == "Administrative / Ceremonial / Government Closure":
        return "Federal Government Operations"
    return "General Public / Multiple Sectors"


def classify_policy_impact(text: str, domain: str, subcategory: str) -> str:
    t = clean_text(text)
    if any(k in t for k in ("national emergency", "terrorism", "critical infrastructure", "border security")):
        return "Critical"
    if any(
        k in t
        for k in (
            "national security",
            "immigration enforcement",
            "civil rights",
            "federal contracting",
            "procurement",
            "tariff",
            "sanction",
            "deregulation",
            "federal workforce",
        )
    ):
        return "High"
    if any(k in t for k in ("program", "initiative", "grant", "task force", "council", "commission", "permit")):
        return "Medium"
    if domain == "Administrative / Ceremonial / Government Closure":
        return "Low"
    return "Medium"


def build_review_flag_and_reason(row: pd.Series) -> tuple[str, str]:
    """Recovered V3-style review controls, expressed transparently."""
    if row["ClassificationMethod"] == "Priority Rule":
        return "No", ""

    reasons: list[str] = []
    score = float(row["ConfidenceScore"])
    secondary = float(row.get("SecondaryScore", 0) or 0)
    source = str(row.get("SourceQuality", ""))

    if score < LOW_CONFIDENCE_THRESHOLD:
        reasons.append("Low NLP confidence")
    if secondary and abs(score - secondary) <= SECONDARY_CLOSE_GAP:
        reasons.append("Close secondary domain")
    if safe_str(row.get("DomainAdjustmentNote", "")):
        reasons.append("Domain adjustment applied")
    if (
        row["PolicyDomain"] == "Administrative / Ceremonial / Government Closure"
        and score < 0.42
    ):
        reasons.append("Low-confidence administrative classification")
    if source.startswith("Weak"):
        reasons.append("Weak source text")

    return ("Yes", "; ".join(reasons)) if reasons else ("No", "")


class ExecutiveOrderClassifier:
    """Hybrid rule + semantic-similarity classifier."""

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        if SentenceTransformer is None:
            raise RuntimeError(
                "sentence-transformers is required for semantic classification. "
                "Install the project dependencies before constructing the classifier."
            )
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.domain_names = list(DOMAIN_DESCRIPTIONS)
        self.domain_embeddings = self.model.encode(
            [DOMAIN_DESCRIPTIONS[d] for d in self.domain_names],
            convert_to_tensor=True,
            show_progress_bar=False,
        )

    def top_domain_matches(self, text: str, top_n: int = 5) -> list[tuple[str, float]]:
        cleaned = clean_text(text)
        if not cleaned:
            return [("Administrative / Ceremonial / Government Closure", 0.0)]

        embedding = self.model.encode(cleaned, convert_to_tensor=True, show_progress_bar=False)
        scores = util.cos_sim(embedding, self.domain_embeddings)[0].cpu().numpy()
        indices = np.argsort(scores)[::-1][:top_n]
        return [(self.domain_names[int(i)], round(float(scores[int(i)]), 3)) for i in indices]

    def classify(self, text: str) -> dict[str, object]:
        rule = priority_rule_classifier(text)
        matches = self.top_domain_matches(text, top_n=5)

        if rule:
            primary = str(rule["domain"])
            score = 1.0
            method = "Priority Rule"
            keywords = ", ".join(rule["keyword_matches"])
            rule_name = str(rule["rule_name"])
            priority_area = str(rule["priority_area"])
            adjustment = ""
        else:
            primary, score = matches[0]
            method = "NLP Similarity"
            keywords = ""
            rule_name = ""
            priority_area = ""
            adjustment = ""

        alternatives = [(d, s) for d, s in matches if d != primary]
        secondary_domain, secondary_score = alternatives[0] if alternatives else ("", 0.0)
        tertiary_domain, tertiary_score = alternatives[1] if len(alternatives) > 1 else ("", 0.0)

        return {
            "PolicyDomain": primary,
            "ConfidenceScore": score,
            "ClassificationMethod": method,
            "RuleName": rule_name,
            "KeywordMatches": keywords,
            "PriorityArea_Prelim": priority_area,
            "SecondaryDomain": secondary_domain,
            "SecondaryScore": secondary_score,
            "TertiaryDomain": tertiary_domain,
            "TertiaryScore": tertiary_score,
            "TopDomainMatches": json.dumps(
                [{"domain": domain, "score": match_score} for domain, match_score in matches]
            ),
            "DomainAdjustmentNote": adjustment,
        }


def classify_dataframe(
    df: pd.DataFrame,
    *,
    classifier: ExecutiveOrderClassifier,
    cache_path: Path | None = None,
    enable_url_text_extraction: bool = True,
) -> pd.DataFrame:
    """Classify one-row-per-document data and append analytical fields.

    URL enrichment is intentionally disabled in this public wrapper until a
    dedicated, tested retrieval module is enabled. The argument is retained so
    the CLI remains compatible with the historical workflow shape.
    """
    del cache_path, enable_url_text_extraction

    result = df.copy()
    result.columns = result.columns.str.strip()
    original_columns = list(result.columns)
    text_columns = _text_columns(result.columns)

    if not text_columns:
        raise ValueError(
            "No usable text columns found; expected title, abstract, summary, or description."
        )

    result["Base_NLP_Text"] = ""
    for col in text_columns:
        result["Base_NLP_Text"] += " " + result[col].fillna("").astype(str)
    result["Base_NLP_Text"] = result["Base_NLP_Text"].str.strip()
    result["SourceTextUsed"] = "Excel Text Only"
    result["SourceURLUsed"] = ""
    result["NLP_Text"] = result["Base_NLP_Text"]
    result["Clean_Text"] = result["NLP_Text"].apply(clean_text)
    result["TextHash"] = result["Clean_Text"].apply(hash_text)
    result["TextLength"] = result["Clean_Text"].str.len()

    class_df = pd.DataFrame([classifier.classify(text) for text in result["Clean_Text"]])
    result = pd.concat([result.reset_index(drop=True), class_df], axis=1)

    result["PolicySubcategory"] = result.apply(
        lambda row: classify_subcategory(row["Clean_Text"], row["PolicyDomain"]),
        axis=1,
    )
    result["PriorityArea"] = result.apply(
        lambda row: row["PriorityArea_Prelim"] if safe_str(row["PriorityArea_Prelim"]) else "Other",
        axis=1,
    )
    result["AffectedSector"] = result.apply(
        lambda row: classify_affected_sector(
            row["Clean_Text"], row["PolicyDomain"], row["PolicySubcategory"]
        ),
        axis=1,
    )
    result["PolicyImpactLevel"] = result.apply(
        lambda row: classify_policy_impact(
            row["Clean_Text"], row["PolicyDomain"], row["PolicySubcategory"]
        ),
        axis=1,
    )
    result["SourceQuality"] = result.apply(
        lambda row: source_quality(str(row["SourceTextUsed"]), int(row["TextLength"])),
        axis=1,
    )

    review = result.apply(build_review_flag_and_reason, axis=1)
    result["ReviewFlag"] = review.apply(lambda value: value[0])
    result["ReviewReason"] = review.apply(lambda value: value[1])
    result["ClassificationVersion"] = CLASSIFICATION_VERSION
    result["ClassifiedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result["ModelName"] = classifier.model_name

    date_col = next(
        (
            col
            for col in (
                "publication_date",
                "PublishedDate",
                "published_date",
                "date",
                "Date",
                "PubDate",
            )
            if col in result.columns
        ),
        None,
    )
    if date_col:
        parsed = pd.to_datetime(result[date_col], errors="coerce")
        result[date_col] = parsed
        result["Year"] = parsed.dt.year
        result["MonthNumber"] = parsed.dt.month
        result["MonthName"] = parsed.dt.month_name()
        result["Quarter"] = "Q" + parsed.dt.quarter.astype("Int64").astype(str)
        result["YearMonth"] = parsed.dt.strftime("%Y-%m")
        result["PublicationDateUsed"] = date_col
    else:
        result["PublicationDateUsed"] = "No date column found"

    derived = [col for col in result.columns if col not in original_columns]
    return result[[*original_columns, *derived]]
