# Power BI

The historical project used Power BI as the analytical presentation layer.

## Core exploration hierarchy

`Year → PolicyDomain → PolicySubcategory → title`

A decomposition tree was used in the later design to support drill-down from aggregate policy activity to individual presidential documents.

## Recovered analytical concepts

- total document counts;
- domain share;
- year-over-year comparison;
- cumulative documents over time;
- dominant domain;
- detail tables with document title/date/domain/subcategory/source links.

See `powerbi/dax/` and `powerbi/power_query/` for sanitized recovered expressions and lineage notes.

No claim is made that every historically discussed visualization was present in the final PBIX.
