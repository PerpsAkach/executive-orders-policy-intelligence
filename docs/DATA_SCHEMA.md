# Data Schema

## Public source fields

Typical source fields include:

| Field | Meaning |
|---|---|
| `document_number` | Federal Register document identifier |
| `title` | document title |
| `abstract` | available source abstract |
| `publication_date` | publication date |
| `citation` | Federal Register citation |
| `type` | document type |
| `agency_names` | associated agency names |
| `html_url` | Federal Register HTML URL |
| `pdf_url` | GovInfo / Federal Register PDF URL |

Historical enriched datasets also included year, quarter, month, week, and period-bucket fields for Power BI analysis.

## Derived classification fields

The public pipeline produces or preserves fields such as:

- `PolicyDomain`
- `PolicySubcategory`
- `PriorityArea`
- `SecondaryDomain`, `SecondaryScore`
- `TertiaryDomain`, `TertiaryScore`
- `AffectedSector`
- `PolicyImpactLevel`
- `ClassificationMethod`
- `ConfidenceScore`
- `ReviewFlag`, `ReviewReason`
- `KeywordMatches`
- `TopDomainMatches`
- `DomainAdjustmentNote`
- `SourceTextUsed`, `SourceURLUsed`, `SourceQuality`
- `ClassificationVersion`, `ClassifiedAt`, `ModelName`
- `TextLength`, `TextHash`
- `Year`, `Quarter`, `MonthNumber`, `MonthName`, `YearMonth`

`ConfidenceScore` is a rule constant or cosine-similarity score depending on classification path; it is not a calibrated probability.
