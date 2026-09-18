"""Command-line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .pipeline import ExecutiveOrderClassifier, classify_dataframe


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classify U.S. presidential documents by policy domain."
    )
    parser.add_argument("input", type=Path, help="Input .csv or .xlsx file")
    parser.add_argument("--output", type=Path, required=True, help="Output .csv or .xlsx file")
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path(".cache/eo_text_cache.json"),
        help="Reserved cache path for retrieval-compatible workflows",
    )
    parser.add_argument(
        "--no-url-extraction",
        action="store_true",
        help="Use only text already present in the input file",
    )
    parser.add_argument("--model", default="all-MiniLM-L6-v2")
    return parser


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError("Input must be CSV or Excel.")


def write_table(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df.to_csv(path, index=False)
    elif suffix == ".xlsx":
        df.to_excel(path, index=False)
    else:
        raise ValueError("Output must be CSV or XLSX.")


def main() -> None:
    args = build_parser().parse_args()
    args.cache.parent.mkdir(parents=True, exist_ok=True)
    df = read_table(args.input)
    classifier = ExecutiveOrderClassifier(args.model)
    result = classify_dataframe(
        df,
        classifier=classifier,
        cache_path=args.cache,
        enable_url_text_extraction=not args.no_url_extraction,
    )
    write_table(result, args.output)
    print(f"Classified {len(result)} rows -> {args.output}")


if __name__ == "__main__":
    main()
