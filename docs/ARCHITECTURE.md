# Architecture

## Current public implementation

The public repository separates ingestion/enrichment, classification, quality controls, export, and BI consumption.

```mermaid
flowchart TD
    FR[Federal Register] --> META[Metadata / URLs]
    GI[GovInfo] --> META
    META --> BASE[Base text assembly]
    BASE --> FETCH[Optional HTML/PDF extraction]
    FETCH --> CLEAN[Text cleaning + hash]
    CLEAN --> RULES[Priority rules]
    RULES -->|No match| EMB[all-MiniLM-L6-v2]
    EMB --> SIM[Cosine similarity]
    RULES -->|Match| PRIMARY[Primary domain]
    SIM --> PRIMARY
    SIM --> ALT[Secondary / tertiary signals]
    PRIMARY --> DERIVE[Subcategory / priority / sector / impact]
    ALT --> QA[Review heuristics]
    DERIVE --> QA
    QA --> OUT[CSV / XLSX]
    OUT --> PBI[Power BI]
```

## Historical evolution

1. CSV/Excel → Power Query → Power BI → keyword classification.
2. RSS experimentation for Federal Register/GovInfo acquisition.
3. Python V1 hybrid rule + semantic classifier.
4. V2 URL enrichment, cache, multi-domain signals and richer provenance.
5. V3 stronger extraction, broader category-adjustment logic and revised review rules.

No production scheduler, database, model registry, or deployment platform is claimed in the recovered evidence.
