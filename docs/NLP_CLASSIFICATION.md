# NLP Classification

## Model

Historical V1, V2 and V3 use SentenceTransformers model `all-MiniLM-L6-v2`.

The model is used as an embedding encoder. The project does **not** fine-tune the transformer and does not contain a supervised training loop.

## Domain taxonomy

The recovered classifier uses 14 primary policy domains:

1. DEI / Civil Rights / Merit
2. Government Efficiency / Federal Workforce
3. Regulation / Deregulation / Administrative Law
4. Economy / Finance / Markets
5. Immigration / Borders / Foreign Nationals
6. National Security / Defense / Foreign Policy
7. Health / Drugs / Family Policy
8. Housing / Infrastructure / Transportation
9. Environment / Energy / Natural Resources
10. Law Enforcement / Public Safety / Justice
11. Technology / AI / Data / Science
12. Education / Sports / Culture
13. Trade / Domestic Production / Buy American
14. Administrative / Ceremonial / Government Closure

Exact domain descriptions and ordered rule dictionaries are preserved in the sanitized `core.py` derivative.

## Hybrid decision flow

Priority rules execute before semantic ranking. If no rule matches, the cleaned document text is embedded once and compared with pre-embedded domain descriptions using cosine similarity.

V3 ranks five domain candidates, then may apply category-adjustment logic for historically over-broad domains including Government Efficiency, Regulation, and Technology.

## Review controls

V3 review logic includes:

- low-confidence threshold: `< 0.30`;
- close secondary-domain gap: `<= 0.04`;
- any category-adjustment note;
- low-confidence administrative classification;
- weak source text.

Priority-rule records bypass those later review checks in the recovered V3 logic.

## Important interpretation

`ConfidenceScore` should not be interpreted as model certainty in a probabilistic sense. Rule matches receive `1.00`; semantic classifications receive cosine similarity. Those values have different meanings.
