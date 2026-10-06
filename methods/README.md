# Completed methods and reproducibility evidence

本目录提供已经实施的方法代码、冻结计划和可在普通电脑运行的配对指标复算入口。`../experiments/EXPERIMENT_INDEX.csv` 对应 38 个方法族以及待完成、历史部分记录；每个方法的结果证据位于索引指定的 ZIP 分卷。原模型权重的可用状态在 `METHODS_MANIFEST.json` 中逐项说明。

## What is included

- `source_code_and_frozen_plans.zip`: original dataset-build, training, inference, classical baseline, rule, router, cache, and independent evaluator sources; includes historical original scripts and later completed implementations.
- `METHODS_MANIFEST.json`: archive checksums, exact recorded environment versions, public base-model identities, packaged/unavailable checkpoint assets, and reproducibility boundaries.
- `PACKAGE_QA.json`: completed archive integrity, private-path/credential screening, and Python-source parsing checks.
- `recompute.py`: portable, standard-library-only exact-rule and frozen-prediction pair metric recomputation.
- `requirements-experiments.txt`: recorded neural package versions and needed unversioned libraries. This is a documented environment starting point; only explicitly recorded versions are pinned.
- `requirements-token-audit.txt`: independently documented tokenizer audit dependencies, kept as a separate workflow.

Each ZIP stores `PROVENANCE_MANIFEST.json` and source files under `source/output/...` or `source/legacy_local/...`. Original source hashes and released file hashes are separate. Private workstation/server path prefixes and any sensitive literals are redacted with an explicit per-file record; the original research files were not changed. Historical internal source hashes are preserved as provenance, so a redacted source archive should not be presented as byte-identical to the original frozen runtime.

The evidence includes actual prediction scores/decisions, summary metrics and independent QA where available, while omitting pretrained/large trained weight bytes, screenshots, repeated tar archives and the large validation-search prediction matrix. Failed approaches and unexecuted plans retain their recorded status. Method families sharing an original output or copied delivery table are not additional independent experiments.

## Portable CPU recomputation

These commands work after cloning and obtaining the corresponding dataset archives. Input files may be plain CSV or CSV.GZ. All paths are explicit arguments; the program uses no server, personal directory, model download or GPU. Use a new output path to preserve earlier results.

```sh
python3 methods/recompute.py exact \
  --data datasets/bidupm12k/canonical/all_pairs_vfinal_12092.csv.gz \
  --filter split_final=locked \
  --reference-status original_reference \
  --output results/exact_locked.json
```

The exact rule requires nonempty equal canonical descriptions and nonempty equal supplied normalized units. It reproduces the archived description/unit rule without inventing unit conversions. To compare all recorded splits, replace the filter with `--group-column split_final`. Training/validation groups remain training/validation diagnostics and must not be called held-out test performance.

Extract a method evidence archive, then recompute a saved scorer's metrics at its already-frozen threshold:

```sh
unzip experiments/original_models_and_classical_baselines__part01.zip -d extracted
python3 methods/recompute.py metrics \
  --predictions extracted/source/output/remote_experiments_20260923/runs/bge_hard_seed_20260904/pair_scores.csv \
  --gold datasets/bidupm12k/canonical/all_pairs_vfinal_12092.csv.gz \
  --score-column score_bge_v2_m3_hard_hard_refined \
  --threshold 9.1875 \
  --group-column evaluation_split \
  --reference-status original_reference \
  --output results/bge_seed20260904.json
```

For binary saved decisions, use `--prediction-column prediction`. If a file has repeated pair IDs for different seeds/policies, add `--condition-column seed --condition-column policy`; conditions automatically become separate metric groups. An undeclared duplicate pair/condition is rejected. The program joins labels only from the supplied reference file and reports unmatched-reference coverage, unknown labels, and unscored predictions. Undefined precision/recall remain `null`. It does not tune thresholds, run models, infer human annotation status, or rerank Top3.

`CPU_RECOMPUTATION_QA.json` records verification against the actual released canonical data and frozen BGE score file. The exact-rule checks reproduce internal locked 260 TP / 0 FP / 23 FN and WSDOT 145 TP / 0 FP / 3 FN. The frozen BGE seed20260904 check reproduces internal locked 274 TP / 1 FP / 9 FN.

## Neural reproduction and result interpretation

Archived original neural runners require the documented base models, frozen train/validation splits and locally configured paths. Several original BGE/Qwen trained checkpoints are not available in this local release. New robust BGE LoRA adapter weights and historical MiniLM weights exist locally but are deliberately excluded from these evidence bundles; do not assume a download link is supplied. Training code, selection histories and saved predictions remain available. No clean-install neural rerun is claimed.

The preserved training and inference dependencies include PyTorch2.8.0/CUDA12.8, Transformers4.57.6 and PEFT0.20.0; actual per-run manifests govern the settings. BF16 scores can vary when batch shapes/runtime settings change. Exact serialization-cache equivalence applies within the same frozen computation setting; it does not establish equivalence between different batch regimes. Engineering parse memoization and serialized model-input caching are separate measured optimizations.

Main dataset references are the original frozen human reference. Challenge600 uses construction-intent labels and has no completed double-human adjudicated gold; it has no formal query pools for Top3. Alberta later comparisons use a frozen AI reference with 56 uncertain pairs and still await human gold. GPT results are Codex independent-agent judgments, not billed OpenAI API measurements. Resident GPU timing/rental amortization excludes model loading, candidate retrieval, human review and full deployment billing.

Complete pair decisions and actual displayed Top3 must remain separate. Preserve rejected, pending, unknown and ranking-displaced rows when interpreting coverage. The full index contains lower-scoring and failed methods; the evidence does not establish one method as best across all datasets, metrics and costs.
