# Provenance

## Evidence labels

- **RECOVERED** — directly supported by surviving project source/artifact evidence.
- **RECONSTRUCTED** — rebuilt because the literal original was unavailable.
- **ENHANCED** — public-repository improvement added during recovery.
- **UNVERIFIED** — remembered or implied but not supported sufficiently.

## Historical source recovery

Three complete generated Python sources were recovered from the original project history. They passed Python syntax parsing during recovery.

| Historical file | Lines | SHA-256 | Status |
|---|---:|---|---|
| `classify_exec_orders_nlp.py` | 498 | `50d42352de5982180496d6fc609597a6dd8c591f8aa8c3924ce0c5378ae4d3c2` | RECOVERED |
| `classify_exec_orders_nlp_v2.py` | 1,150 | `58e3c6662386cd9b2624445555db2d3b12ceccc6537e398d9818c8b1613e5e7a` | RECOVERED |
| `classify_exec_orders_nlp_v3.py` | 1,265 | `027ed1aae1d27cc0e55d6b33ac3da2170ff9fe2527d8835485b88600ca7781c3` | RECOVERED |

The historical sources contain private work-folder paths and are therefore not published verbatim in this public repository.

## Public source boundary

`src/executive_order_intelligence/core.py` is a **SANITIZED DERIVATIVE** of the recovered V3 core classification logic. Private paths and top-level workflow execution were removed.

`src/executive_order_intelligence/pipeline.py` and `cli.py` are **ENHANCED** public wrappers that make the workflow portable and testable. They should not be represented as the exact historical source.

## Recovered run evidence

A historical V2 execution reported 480 processed rows and successful Excel export. It also reported 424 review flags and 56 non-review records. The resulting 88.3% review rate is a workflow statistic, not an accuracy metric.

## Not recovered as original data files

- populated V2/V3 text-cache JSON files;
- historical local model cache/weights;
- classified V1/V2/V3 workbook contents;
- any later local edits made after the recovered generated sources.

## Claims intentionally excluded

The repository does not claim formal classification accuracy, precision, recall, F1, calibrated probabilities, supervised training, fine-tuning, production scheduling, CI/CD in the historical implementation, or production database deployment.
