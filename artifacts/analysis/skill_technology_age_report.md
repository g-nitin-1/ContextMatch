# Skill Technology-Age Scan

Scan version: `skill-tech-age-scan-0.1.0`
As of: `2026-06-01`

This is a post-freeze diagnostic. It is not a hard integrity gate.

## Summary

- Candidates scanned: 100,000
- Dated skill names checked: 22
- Checked dated-skill mentions: 91,050
- Unique candidates with at least one issue: 1,355
- Total skill-duration issues: 1,541
- Frozen Idea2 top-100 candidates with issue: 81
- Team Qwen top-100 candidates with issue: 81

## Counts By Skill

| Skill | Release date | Age months | Candidates with skill | Violating candidates |
|---|---:|---:|---:|---:|
| QLoRA | 2023-05-23 | 37 | 1401 | 414 |
| LlamaIndex | 2023-02-16 | 40 | 1308 | 341 |
| PEFT | 2023-01-19 | 41 | 1377 | 315 |
| LangChain | 2022-10-25 | 44 | 5162 | 282 |
| OpenSearch | 2021-09-20 | 57 | 1286 | 77 |
| Qdrant | 2021-02-09 | 64 | 1379 | 25 |
| LoRA | 2021-06-01 | 60 | 1371 | 24 |
| Pinecone | 2020-12-31 | 66 | 5062 | 18 |
| pgvector | 2021-06-12 | 60 | 1394 | 16 |
| Weaviate | 2019-11-04 | 79 | 1389 | 8 |
| Haystack | 2019-11-28 | 79 | 1333 | 6 |
| Sentence Transformers | 2019-07-25 | 83 | 5081 | 6 |
| Milvus | 2019-06-16 | 84 | 1384 | 5 |
| Hugging Face Transformers | 2018-11-17 | 91 | 5163 | 4 |
| Docker | 2013-03-20 | 159 | 12062 | 0 |
| FAISS | 2017-02-01 | 112 | 5052 | 0 |
| FastAPI | 2018-12-05 | 90 | 11917 | 0 |
| Kubernetes | 2014-06-07 | 144 | 12071 | 0 |
| PyTorch | 2017-01-19 | 113 | 1378 | 0 |
| React | 2013-05-29 | 157 | 11811 | 0 |
| TensorFlow | 2015-11-09 | 127 | 1381 | 0 |
| scikit-learn | 2010-02-01 | 196 | 1288 | 0 |

## Violating Candidates By Archetype

| Archetype | Unique candidates |
|---|---:|
| applied_ml | 130 |
| data_backend_adjacent | 341 |
| general_software | 709 |
| generic_ml | 152 |
| senior_explicit_ai | 17 |
| senior_plain_language | 6 |

## Interpretation

Skill-duration chronology is a data-quality diagnostic, not a hard honeypot rule, because violations are broad across strong cohorts and occur in structured skill metadata.

The large top-100 hit rate means this signal should not be promoted to a hard honeypot rule without external confirmation. It is better treated as evidence that `skills.duration_months` is generated from candidate seniority rather than from each technology's true age.

