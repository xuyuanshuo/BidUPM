# Dataset download archives

These 28 independent ZIP archives contain the complete packaged `datasets/`
directory. They are grouped by dataset and each stays below the browser upload
limit. `manifest.json` records every ZIP and every member's SHA-256 and size.

The Alberta dataset is in `alberta-001.zip` and `alberta-002.zip`;
`alberta_historical-001.zip` contains the earlier code-anchor and price study.
The current main benchmark is in `bidupm12k-001.zip` and
`bidupm12k-002.zip`, and the diagnostic 600-pair set is in
`challenge600-001.zip`. Keep all numbered archives for a dataset together.

From the cloned repository, restore the archived tree and check its hashes:

```sh
python scripts/materialize_datasets.py --restore-archives data_archives --restore-only
python scripts/verify_datasets.py
```

To write decompressed Alberta files into a separate local directory:

```sh
python scripts/materialize_datasets.py --dataset alberta --output-dir materialized
```

The large NCDOT full-pair CSV is already present losslessly as 11 gzip shards.
Reconstruct its original 8,518,172 rows only when needed:

```sh
python scripts/materialize_datasets.py --dataset ncdot_raw --output-dir materialized
```

The decompressed full-pair CSV uses about 5 GB. The verifier can validate its
joined bytes by streaming, without writing that large file. Manual ZIP
extraction into the repository root is also possible, but the supplied restore
command verifies hashes and rejects unsafe archive paths.

Each dataset is split into independent ZIP archives; the inventory lists every file and checksum. Original Excel, CSV, annotation, dataset-card, and source evidence files are retained in the archives. Run the restore command after cloning to recover the complete tree; no additional Python packages are required. Label types and data-rights status are documented in `datasets/README.md`.
