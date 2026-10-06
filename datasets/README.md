# BidUPM datasets

This package preserves the current benchmark, every identified distinct historical corpus, available source materials, and all observed Alberta experiment inputs. Labels are kept exactly as supplied; privacy redactions apply only to local paths and explicit connection metadata in text files.

| Folder | Contents | Label status |
|---|---|---|
| `bidupm12k/` | 12,092 canonical pairs; 4,138 training rows; validation and held-out partitions; annotation and provenance | Final human-reviewed/adjudicated labels; use `split_final` and `final_label` |
| `challenge600/` | 600 controlled pairs from 300 real-source anchors; model-only and annotation-blind inputs | Provisional construction labels; independent human review incomplete |
| `alberta/` | Original bid form and complete UPA workbook; 135 queries; 237 candidates for 2024 and 264 for 2026; 67,635 pairs per current representation | Unlabeled; AI review references are separate and provisional |
| `alberta_historical/` | 2019–2026 UPA items, cross-year code anchors and earlier price case data | Deterministic code anchors; derived price predictions |
| `historical/provenance_v2/` | Earlier NCDOT source-restricted corpus and human seed | Human seed with pending review rows |
| `historical/price_case_v1/` | Earlier query/candidate/price corpus and review queues | Confirmed seed and pending candidates |
| `historical/gpt55_expanded/` | 5,702 pairs: 1,270 human seed plus 4,432 AI adjudications | Mixed human/AI provenance; not all human gold |
| `historical/confirmed_gold_20260511/` | 3,000 confirmed pairs; derived 2,879 hard-no-exact pairs | Historical confirmed gold |
| `source_materials/` | Available original NCDOT forms; user-supplied form; normalized source items; frozen retrieval/query selections | Raw and provisional retrieval artifacts |
| `ncdot_raw/` | 59,004 source items; 144,993 prices; 271,938 capped and 8,518,172 full exact-rule mined pairs | Rule-mined positives are not human gold |

## Format and integrity

`manifest.json` records stored-file SHA-256, decompressed SHA-256, original source SHA-256, schema columns and row counts where available. Identity and gzip are the storage encodings. Gzip members have deterministic metadata (`mtime=0`, empty filename). Files over 10 MiB are compressed. Every stored file is below 20 MiB.

The original 4,938,246,689-byte full mined-pair CSV is represented losslessly by 11 ordered gzip shards in `ncdot_raw/full_pairs/`. Its nested manifest repeats the original header in each shard and specifies how to skip later headers when joining. Full-source SHA-256: `33bed8dd441271402fefb7e2197fc161707640d55ec9bc2e9eee36c80f307882`.

Byte-identical duplicates have SHA aliases in the main manifest. The materialization tool restores their logical paths. Existing source data cards and historical proposal manifests are preserved as historical evidence; current per-folder READMEs state the applicable label status.

## Source coverage and reuse

Eight original WSDOT source workbooks named by canonical provenance were not found locally. Their parsed source rows and public URLs are retained; the main manifest records this gap explicitly. Source licence/redistribution rights are not established by the supplied evidence, including the user-supplied form. Original public agency materials retain their owners' rights; this package does not invent a blanket data licence. Original binary workbook bytes are preserved.

## Usage notes

Train only on the current `bidupm12k/training/` partition, and select thresholds on validation only. Report Locked, No-reference, and External partitions separately. Alberta has no independent human-adjudicated gold; its AI first pass is not human gold. Analyze the 600-pair diagnostic set by its 300 anchors and retain its construction labels. The full raw rule-mined collection is not human semantic gold. Historical versions are retained independently and must not be merged into the current test set when interpreting metrics.
