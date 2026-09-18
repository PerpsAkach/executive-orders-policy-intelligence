from executive_order_intelligence.core import (
    classify_subcategory,
    clean_text,
    hash_text,
    priority_rule_classifier,
)
from executive_order_intelligence.pipeline import source_quality


def test_clean_text_normalizes_case_spacing_and_punctuation():
    assert clean_text("  Artificial   Intelligence, Policy! ") == (
        "artificial intelligence  policy"
    )


def test_hash_text_is_stable_and_short():
    assert hash_text("example") == hash_text("example")
    assert len(hash_text("example")) == 16


def test_dei_priority_rule_precedes_semantic_classification():
    result = priority_rule_classifier(
        "This directive addresses diversity, equity, and inclusion programs."
    )
    assert result is not None
    assert result["domain"] == "DEI / Civil Rights / Merit"


def test_immigration_priority_rule():
    result = priority_rule_classifier(
        "The order concerns visa entry and immigration enforcement."
    )
    assert result is not None
    assert result["domain"] == "Immigration / Borders / Foreign Nationals"


def test_subcategory_is_deterministic_within_domain():
    subcategory = classify_subcategory(
        "federal contracting procurement acquisition requirements",
        "Government Efficiency / Federal Workforce",
    )
    assert subcategory == "Federal Contracting / Procurement"


def test_source_quality_heuristics():
    assert source_quality("Full Text - HTML", 13000) == "Strong - Full Text"
    assert source_quality("Excel Text Only", 1200) == "Moderate - Excel Text"
    assert source_quality("Excel Text Only", 200) == "Weak - Short Text"
