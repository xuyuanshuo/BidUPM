# BidUPM

**Construction bid-item matching datasets and experimental evidence.**

This repository packages the current research data and distinct historical
versions, including the original Alberta bid form, UPA workbooks, and all
current candidate-pair representations. Files are organized by source, version,
use, and label status. Provenance notes, frozen records, field definitions, and
SHA-256 checksums are retained. Snapshot date: **2026-10-05**.

## Datasets

| Dataset | Contents and scale | Label status |
|---|---|---|
| [BidUPM-12k](docs/DATASET_CARDS.md#bidupm12k) | 12,092 pairs; training, validation, locked test, no-reference, and external partitions | Human-reviewed and adjudicated; initial proposal columns are historical only |
| [Alberta](docs/DATASET_CARDS.md#alberta) | 135 queries; 237 UPA 2024 items and 264 UPA 2026 items; 67,635 candidate pairs | Inputs are unlabeled; AI reference labels and a blank human-review template are separate |
| [Challenge600](docs/DATASET_CARDS.md#challenge600) | 600 pairs constructed from 300 real-source anchors | Construction-intent labels; independent human annotation is incomplete |
| [Historical Alberta](docs/DATASET_CARDS.md#alberta_historical) | 2019–2026 UPA entries, cross-year code anchors, and price cases | Code rules and derived price-study outputs |
| [Historical versions](datasets/README.md) | Source corpora, price cases, GPT-5.5 expansion, and historical confirmed sets | Human, AI, and pending-review status are recorded separately |
| [Raw NCDOT](docs/DATASET_CARDS.md#ncdot_raw) | 59,004 bid-item rows, 144,993 price records, and 8,518,172 rule-mined pairs | Raw source data and deterministic rule labels |
| [Source materials](docs/DATASET_CARDS.md#source_materials) | Original bid tabs, normalized records, and historical retrieval candidates | Source and candidate-generation evidence |

The complete packaged-file inventory is in [datasets/manifest.json](datasets/manifest.json).
Transport archives are in [data_archives/](data_archives/README.md). Field
formats and readers are described in [docs/DATA_FORMAT.md](docs/DATA_FORMAT.md).

**Alberta AI references and the constructed Challenge600 labels are not
independent human gold standards.** Historical versions must not be merged with
the current canonical sets when computing paper metrics.

## Download and restore

Git and Python 3.10 or later are required. The restoration and verification
tools use only the Python standard library.

```sh
git clone https://github.com/xuyuanshuo/BidUPM.git
cd BidUPM
python scripts/materialize_datasets.py --restore-archives data_archives --restore-only
python scripts/verify_datasets.py
```

Twenty-eight independent ZIP archives preserve the complete packaged dataset
tree (about 281 MiB). Restoration verifies each archive and member hash before
writing the files. Large CSV files remain gzip-compressed and can be expanded on
demand:

```sh
python scripts/materialize_datasets.py --dataset alberta --output-dir materialized
python scripts/materialize_datasets.py --dataset bidupm12k --output-dir materialized
```

The large raw-pair CSV is stored losslessly as 11 ordered shards. To reconstruct
the approximately 5 GB CSV explicitly:

```sh
python scripts/materialize_datasets.py --dataset ncdot_raw/full_pairs --output-dir materialized
```

You can also download the repository through GitHub's **Code → Download ZIP**
and run the same commands.

## Methods and experiments

[docs/METHODS.md](docs/METHODS.md) records the classical baselines, BGE/Qwen
adaptation and ranking, verification, rule-first routing, caching, diagnostic
sets, and Alberta transfer experiments. The [experiment index](experiments/EXPERIMENT_INDEX.csv)
records completion status and authoritative evidence paths. [methods/](methods/README.md)
contains the method code, CPU replay utility, and reproducibility conditions;
[experiments/](experiments/README.md) contains the released experiment evidence.

Pair quality must be reported separately from the actual at-most-three returned
results. The primary evaluation uses 218 queries; the 220-query timing scope
includes two reclassified audit pools. Thresholds are selected on validation;
test and Alberta outputs are not tuning data. The three existing adapter seeds
and the single-seed new LoRA experiments are identified separately.

The original BGE/Qwen training weights were not found in the accessible local
materials. Frozen scores and results can be audited, but a fresh neural rerun
still requires the corresponding weights and runtime environment.

## Sources, licensing, and citation

Source URLs for third-party data are retained in the source manifests. Eight
original WSDOT workbooks were not found locally; their parsed records and public
URLs are retained, and the gap is documented in the dataset cards.

Original source filenames, workbook text, and annotation rationales are preserved
verbatim when needed for provenance; those source records may contain non-English
text even though the repository documentation is English.

The [MIT license](LICENSE) covers only the original data tooling in `scripts/`.
Rights for the data and pre-existing experiment materials are described in
[DATA_LICENSE.md](DATA_LICENSE.md); this snapshot does not assign a uniform data
license. Cite this snapshot with [CITATION.cff](CITATION.cff) and preserve the
original source attribution.
