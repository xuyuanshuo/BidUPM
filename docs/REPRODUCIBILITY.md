# Reproducibility of this snapshot

## Data layer

1. Clone or download the repository.
2. Restore `data_archives` using `scripts/materialize_datasets.py --restore-archives data_archives --restore-only`.
3. Run `scripts/verify_datasets.py` for packaged and decompressed hashes, recorded row counts, model-input label exclusions, and large-shard byte reconstruction.
4. Materialize selected datasets into a separate `materialized/` directory as described in the main README.

The archive manifest identifies the transport ZIPs and each member. The dataset
manifest identifies the packaged files, source hashes, compression and recorded
text-metadata redactions. Original and packaged hashes differ only when a
recorded transformation was necessary; privacy path changes must not be mistaken
for unchanged bytes. SHA aliases identify byte-identical source files without
duplicating payloads.

## Scientific layer

Use the current canonical `split_final`, `final_label`, and `final_relevance`
fields, not initial proposals. Keep training eligibility and evaluation exclusions.
The additional no-reference file overlaps the main evaluation and is not an
independent dataset. Preserve frozen candidate pools, input serialization,
validation thresholds and seed scope when comparing the original experiments.

Independent human evaluation, AI reference comparison, rule-derived labels and
construction intention labels describe different evidence. Dataset cards state
which is available. Do not combine their scores as though they share a reference
standard.

## Method layer

The method documentation and experiment index distinguish completed model
inference, CPU score replay, actual runtime measurements, diagnostics, partial
runs and unexecuted conditions. Original experiment sources are archived with
their provenance; private local paths may be redacted in the published copies.
The portable CPU utility is for recomputing metrics and a documented exact-text
rule. It does not reproduce unavailable neural weights or original server timing.

The dataset integrity workflow uses a fresh repository checkout and requires
only Python. Model training and inference have their own dependencies and
hardware requirements, described in `methods/`.
