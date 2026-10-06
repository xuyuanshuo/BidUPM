# Dataset cards / 各数据集说明

The complete directory is restored from `data_archives/`. These cards are also retained inside those archives.


## alberta

Raw inputs: Owner Bid Form 135 rows; UPA 2024 has 237 catalog rows and UPA 2026 has 264. Raw workbooks retain all historical sheets (2019–2026). Complete query-candidate Cartesian products: 31,995 pairs for 2024 and 35,640 for 2026, 67,635 per current input representation (raw, cleaned, scope_core). September 29 inputs preserve the earlier 2024 experiment format. Two queries have missing unit fields in the audited raw form. No adjudicated independent human semantic gold is available. AI first-pass labels and newer AI references are provisional review evidence; the human gold workbook is a blank template. Do not report accuracy/F1 from unlabeled data or AI reference as human gold. Equal text/unit candidate coverage is distinct from semantic correctness. Query tender date is unverified. Never tune frozen thresholds on Alberta outputs. Original binary workbook bytes are preserved; textual metadata has privacy path redactions.

Source reuse/license status: not established in the supplied evidence. Original public agency materials retain their owners' rights. No new blanket data licence is granted by this package.


## alberta_historical

2019–2026 UPA entries and code-anchored cross-year pairs preserved from an earlier experiment, plus held-out 2026 price-case outputs and provenance. Code anchors are deterministic identities and are not independently human-reviewed semantic-match labels. Price-case predictions are derived results; they must not be confused with the current 135-query bid-form evaluation.

Source reuse/license status: not established in the supplied evidence. Original public agency materials retain their owners' rights. No new blanket data licence is granted by this package.


## bidupm12k

12,000 corrected core pairs plus 92 training-only hard positives (12,092 total). Use `split_final`, `final_label`, `final_relevance` and `training_eligibility`; initial proposal/split columns remain for history. Train from `training/` only. Tune thresholds on validation only. Canonical training: 4,138 rows; directional deduplicated training: 2,278 rows. Main evaluation: locked 3,000/100 queries, original no-reference 1,140/38, external 2,400/80; two reclassified audit pools add 60/2. Validation is 900/30. The additional no-reference safety file has 1,710 pairs/57 queries (38 original + 19 external), and is a derived overlapping subset. Historical source/proposal manifests are preserved and are not the current label/split authority. Six A/B source workbooks and adjudication evidence are included. A .gz suffix means decompress before reading; SHA aliases are listed at the top manifest.

Source reuse/license status: not established in the supplied evidence. Original public agency materials retain their owners' rights. No new blanket data licence is granted by this package.


## challenge600

600 constructed pairs clustered into 300 real-source anchors; 300 provisional positives and 300 single-attribute negatives. Construction labels are provisional; independent human annotation is incomplete. Source contracts are excluded from canonical benchmark contracts. Version v3 (observed dimension values) is frozen; obsolete v1/v2 snapshots are omitted. Model input files omit labels and transformation rationale. Do not treat this as a naturally occurring 600-project corpus or human gold. Prospective natural candidate mining evidence is separate under natural_candidate_mining/.

Source reuse/license status: not established in the supplied evidence. Original public agency materials retain their owners' rights. No new blanket data licence is granted by this package.


## historical/confirmed_gold_20260511

3,000 confirmed pairs from 100 query pools; a derived hard-no-exact subset contains 2,879 pairs. Earlier Qwen annotation records and risk appendices are retained as annotation evidence. Some derived result tables are included for provenance. Three byte-identical unpacked copies have been deduplicated. This older corpus does not replace current canonical labels/splits.

Source reuse/license status: not established in the supplied evidence. Original public agency materials retain their owners' rights. No new blanket data licence is granted by this package.


## historical/gpt55_expanded

Distinct earlier corpus/version retained for reproducibility. Consult SOURCE_README.md and source data cards for historical scope and annotation status. These files do not replace the 12,092-pair canonical benchmark. GPT-adjudicated or pending review rows must not be described as human gold. Duplicate source hashes are represented by aliases in datasets/manifest.json.

Source reuse/license status: not established in the supplied evidence. Original public agency materials retain their owners' rights. No new blanket data licence is granted by this package.


## historical/price_case_v1

Distinct earlier corpus/version retained for reproducibility. Consult SOURCE_README.md and source data cards for historical scope and annotation status. These files do not replace the 12,092-pair canonical benchmark. GPT-adjudicated or pending review rows must not be described as human gold. Duplicate source hashes are represented by aliases in datasets/manifest.json.

Source reuse/license status: not established in the supplied evidence. Original public agency materials retain their owners' rights. No new blanket data licence is granted by this package.


## historical/provenance_v2

Distinct earlier corpus/version retained for reproducibility. Consult SOURCE_README.md and source data cards for historical scope and annotation status. These files do not replace the 12,092-pair canonical benchmark. GPT-adjudicated or pending review rows must not be described as human gold. Duplicate source hashes are represented by aliases in datasets/manifest.json.

Source reuse/license status: not established in the supplied evidence. Original public agency materials retain their owners' rights. No new blanket data licence is granted by this package.


## ncdot_raw/NCDOT_Raw_Parsed

This package parses the downloaded public NCDOT XLS bid-tab files into row-level bid items and bidder price records.

| Item | Count |
| --- | ---: |
| Parsed files | 39 |
| Parse-ok files | 39 |
| Bid item rows | 59004 |
| Bidder price records | 144993 |
| Raw rule-exact positive pairs | 8518172 |
| Capped rule-exact positive pairs | 271938 |

The exact-positive pool requires equal normalized description and unit and different source files.


## ncdot_raw

59,004 raw bid-item rows and 144,993 raw price records from 39 parsed public bid-tab workbooks. Deterministic exact-rule mined pairs are separate: capped 271,938 rows and full 8,518,172 rows. These rule-exact positives are not human-reviewed semantic gold. The full 4.94GB source CSV is losslessly represented as ordered gzip shards with its original header repeated. Use full_pairs/manifest.json to reconstruct the original bytes and verify the full-source hash. Raw HTML listing, source recheck and download/parse manifests are retained. Source reuse/license status is unknown.

Source reuse/license status: not established in the supplied evidence. Original public agency materials retain their owners' rights. No new blanket data licence is granted by this package.


## source_materials

Original available NCDOT central-let bid-tab workbooks and the historical user-supplied bid form. The all_bid_items_raw_normalized table retains parsed NCDOT/WSDOT/Caltrans records and price fields. Frozen Top-100 retrieval tables/query selections are historical candidate-generation artifacts with provisional labels, not current gold. Eight WSDOT source workbook names appear in canonical provenance but the original Excel bytes were not found locally; their public URLs and parsed rows are retained. SHA aliases refer to identical original files already stored under ncdot_raw. User-supplied form publication rights are not established.

Source reuse/license status: not established in the supplied evidence. Original public agency materials retain their owners' rights. No new blanket data licence is granted by this package.
