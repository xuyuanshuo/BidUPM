# Dataset formats, integrity and restoration

The release preserves the source datasets, annotation evidence and model inputs as separate files. Read each dataset's `README.md` before selecting a training or evaluation input. Label quality differs across datasets; an AI reference or a deterministic rule match does not establish a human-reviewed gold label.

## Restore a downloaded repository

The public repository stores the bulk dataset bytes in `data_archives/` as small ZIP transport files. Dataset cards and release manifests are also visible directly under `datasets/`. Use Python 3.10 or later; the scripts require only the standard library.

From the repository root:

```sh
python scripts/materialize_datasets.py --restore-archives data_archives --restore-only
python scripts/verify_datasets.py --check-repository-size
```

The first command restores the packaged files to their recorded `datasets/...` paths and verifies their sizes and SHA-256 hashes. It reuses an existing file only when its bytes match the transport manifest. The second command also reads every gzip payload, checks recorded CSV/JSONL row counts, checks CSV column names/order and validates the complete large-pair reconstruction without writing a large output file. Full verification processes several gigabytes of decompressed data and takes longer than checking packaged hashes. `--quick` checks compressed/stored hashes and sizes while skipping payload and reconstruction checks.

To obtain ordinary uncompressed files for a selected dataset:

```sh
python scripts/materialize_datasets.py --dataset alberta --output-dir data
python scripts/materialize_datasets.py --dataset bidupm12k --output-dir data
```

Selection accepts an ID from `datasets/manifest.json` or a relative path prefix and can be repeated. The output directory must be outside the packaged `datasets/` directory. Running without a selection restores ordinary datasets but skips the large raw-pair reconstruction. The scripts refuse to replace a differing existing file unless `--overwrite` is supplied.

## CSV and annotation fields

CSV headers and their order are recorded per file in the manifest. Row counts exclude the header. The default text encoding is UTF-8 with an optional byte-order mark; a file can record a different `text_encoding` or `delimiter` when necessary. Newlines, quoting and source bytes are preserved during restoration. Use a CSV parser rather than splitting lines or counting physical newlines.

For the current BidUPM benchmark, `datasets/bidupm12k/schema.json` identifies `split_final` as the authoritative split field and `final_label` as the authoritative label field. Historical proposal fields and the earlier `split` field remain in source evidence for traceability. Use the recorded final fields for the current benchmark.

Rows with `role: "model_input"` are checked against their `forbidden_columns` list, plus the standard `label`, `gold_label`, `ground_truth` and `matched_label` names. These checks apply to CSV header names and JSONL object keys. They check release schemas; downstream code must still select the intended input columns and keep annotations out of model prompts.

XLSX, PDF, DOCX, ZIP and other binary evidence is verified by its stored and published-payload hashes. The verifier does not infer spreadsheet sheet counts or labels from binary workbooks. JSONL/NDJSON rows are nonblank JSON objects, one object per line.

## Release manifest

`datasets/manifest.json` uses `schema_version: 1`. Each `files` record describes a path relative to the directory holding that manifest.

| Field | Meaning |
| --- | --- |
| `path` | Safe relative path of the packaged file. |
| `sha256`, `size_bytes` | Exact stored-file digest and size, including gzip bytes when compressed. |
| `encoding` | `identity` for unchanged packaging or `gzip` for deterministic compression. |
| `uncompressed_sha256`, `uncompressed_bytes` | Exact published payload after decompression. |
| `source_sha256`, `source_bytes` | Original local source digest and size, retained for provenance. |
| `privacy_redactions` | Recorded changes to metadata before publication. When nonzero, source and published payload bytes may differ. |
| `rows`, `columns` | Optional expected row count and ordered CSV headers. |
| `role`, `forbidden_columns` | Optional model-input classification and annotation columns that must be absent. |
| `nested_manifest` | Explicitly identifies another release manifest to verify recursively. |
| `materialized_path` | Optional relative filename to use after decompression; otherwise the final `.gz` suffix is removed. |

Native historical files named `manifest.json` remain evidence. Only records marked `nested_manifest: true` (or the compatible `submanifest: true`) are interpreted as nested release manifests. A `manifests` list can also reference nested release manifests explicitly.

The top manifest records dataset IDs, paths, label status, license status, duplicate-source aliases and known missing source files. Aliases identify byte-identical source evidence already stored at `canonical_path`; they are not additional dataset examples. Materialization restores an alias at its recorded logical path when that path matches the selected dataset, even if the canonical source belongs to another dataset folder. It first verifies the canonical packaged file, then decompresses it when necessary and checks the restored alias against `source_sha256` and `source_bytes`. Packaging suffixes are removed without changing the logical file extension. Transport-only restoration retains the indexed package layout; logical aliases are created during ordinary materialization. Generated cards and metadata are indexed alongside source files.

When redactions are absent, the verifier can use `source_sha256` and `source_bytes` as fallback payload checks if published-payload fields are unavailable. Original provenance hashes never substitute for published-payload hashes when redactions are recorded.

## Large raw-pair shards

`datasets/ncdot_raw/full_pairs/manifest.json` records an ordered list of independently readable gzip CSV shards. Each shard includes the original header. `header_hex` preserves its exact bytes, including the byte-order mark and line ending. Reconstruction keeps the first header and removes exactly those repeated header bytes from each subsequent shard. The resulting stream must match `full_source_sha256` and `full_source_bytes`, and the shard row counts must sum to `rows`.

Reconstruct the full raw-pair CSV explicitly:

```sh
python scripts/materialize_datasets.py --dataset ncdot_raw/full_pairs --output-dir data
```

The current manifest records 8,518,172 rule-derived pairs and a reconstructed file size of 4,938,246,689 bytes. They are deterministic exact-rule positives with no human review; preserve that distinction in experiments. To reconstruct large sharded data together with all other datasets, add `--reconstruct-large`.

## ZIP transport and archive extraction

`data_archives/manifest.json` contains an `archives` list. Each archive records `path`, `sha256`, `size_bytes` and a `members` list with the same fields for each repository-relative member. Transport members must live beneath `datasets/`. Before restoration, the script checks archive hashes, the exact member inventory, member sizes and safe destination paths; it checks each member digest as its bytes are written. Transport ZIPs are a delivery layer around the individually manifested dataset files.

For an original recorded ZIP/TAR dataset archive, add `--extract-archives` to a materialization command. The original archive is retained and extracted contents are placed beside it under `<archive-name>.extracted/`. Both transport restoration and archive extraction reject absolute paths, `..` traversal, backslash/drive paths, symlinks, hard links, special files and duplicate member paths. Extraction validates the member list before writing and enforces a configurable expanded-size ceiling (`--max-expanded-gib`, default 50 GiB).

The GitHub workflow restores transport files and runs full integrity checks on pushes and pull requests that affect the datasets or restoration tools. It also rejects repository files larger than 25 MiB.
