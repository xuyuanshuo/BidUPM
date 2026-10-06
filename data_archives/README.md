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

数据按数据集分成独立 ZIP；全部文件及其校验值见清单。原始 Excel、CSV、标注、
数据卡和来源证据均保留在包内。下载仓库后运行还原命令即可获得完整目录，
无需安装额外 Python 库。各标签类型和数据权利状态见 `datasets/README.md`。
