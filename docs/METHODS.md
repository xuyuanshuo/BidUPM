# Methods and experiment provenance

This release includes datasets plus archived source code, frozen plans, completed experiment summaries and selected prediction evidence. `methods/METHODS_MANIFEST.json` and `experiments/ARTIFACTS_MANIFEST.json` specify the actual packaged files, hashes and private-path redactions. `experiments/EXPERIMENT_INDEX.csv` distinguishes completed, partial and unexecuted conditions. Original neural weights are not fully distributed; archived server scripts require the dependencies and checkpoint assets described in `methods/README.md`.

This release prioritizes the data layer and includes the implemented method code, frozen plans, experiment summaries, and selected real-prediction evidence. The archive inventory records every included file, checksum, and path redaction; incomplete conditions are listed separately from completed methods. `output/...` entries in the index preserve source-workspace paths, while the archive column points to the packaged repository evidence. Missing model weights and runtime conditions are documented in `methods/README.md`.

## Task and evaluation contract

The task is bid-item compatibility matching for unit-price reference. A model accepts compatible candidate items, then a separate ranking policy may display at most three. Complete pairwise classification, accepted-list recall, and displayed Top3 quality are distinct evaluations. A three-item display must not silently replace complete candidate processing.

The frozen BidUPM collection contains 12,092 labeled pairs / 481 queries. Eligible training has 4,138 source rows, reduced to 2,278 semantic-unique pairs; symmetric augmentation yields 4,556 training examples. Validation uses 900 pairs / 30 queries. Primary held-out evaluation comprises 6,540 pairs / 218 queries: 3,000 internal locked pairs, 1,140 internal no-reference pairs, and 2,400 external WSDOT pairs. The common 6,600-pair / 220-query deployment input additionally includes 60 pairs / 2 audit queries. The 7,500-row saved model outputs include validation. These sizes cannot be interchanged.

## Original baselines and domain-adapted models

| Family | Actual method/configuration | Evidence |
| --- | --- | --- |
| Text and feature baselines | TF-IDF, BM25, supervised feature model (`feature_full`), exact-description/unit rules; some exact-rule analyses are post hoc | Original local experiment outputs and matched comparison table |
| BGE scorer | `BAAI/bge-reranker-v2-m3`; zero-shot, `standard`, `hard_selection_only`, `hard_weight_only`, `hard_refined` | Original/extended manifests, validation histories, 7,500-row pair scores |
| BGE trained input ablations | Full input, description only, no unit, no category/specifications; three original seeds for hard-refined settings | `remote_experiments_20260923/runs` |
| Qwen rerankers | `Qwen3-Reranker-0.6B` standard/hard-refined and `Qwen3-Reranker-4B` standard; zero-shot references | Original/extended run manifests and pair scores |
| Open local verifier | Released `Qwen3-4B-Instruct-2507`, yes-minus-no score, validation-selected threshold 12.75 | Verifier manifest, thresholds, exhaustive and routing outputs |
| Other historical baselines | MiniLM cross-encoders, sentence embeddings, bidirectional refinement and full-corpus retrieval | Original local experiment outputs; retained as historical methods |

Five-field scorer inputs use raw description, normalized description, normalized pay unit, category, and specification tokens. The old training protocol uses positive-class-weighted binary cross entropy and symmetric pair augmentation. Hard-positive sample weight is 3 in hard-weighted regimes. `standard` selects checkpoints by validation overall F1; `hard_refined` uses 0.60 overall F1 + 0.40 hard-pair F1 for checkpoint selection. The original acceptance threshold maximizes validation overall F1. Weighting, threshold selection, and checkpoint selection are separate choices.

The three original seeds are 20260904, 20260905, and 20260906. A second selector may point to the same checkpoint and reuse identical scores; it is not an additional independent training run. Original neural runs record PyTorch 2.8.0 with CUDA 12.8, Transformers 4.57.6, PEFT 0.20.0, BF16 evaluation, and an NVIDIA RTX 4090. BGE's recorded revision is `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`. Per-run manifests take precedence over this summary.

## Deployment and exploratory methods

| Family | Actual behavior | Status and boundary |
| --- | --- | --- |
| Historical query early stop | Exact description/unit acceptance; if a query has three exact candidates, skip its remaining model scores | Completed reference; unscored pairs remain unknown. Not complete-pair evaluation |
| Complete exact-pair route | Accept exact pairs, score all nonexact pairs with frozen BGE; optionally verify BGE-positive nonexact pairs with local Qwen | Actual GPU outputs and timings. Top3 is a separate display policy |
| Generic dimension gate | Accept exact pairs; reject only known incompatible physical/count dimensions; defer unknown, lump-sum, and same-dimension cases to BGE | Actual full-source GPU deployment; input-only rules, no difficulty-label routing |
| Optional engineering size gate | Add train/validation-frozen physical-size contradiction checks | Actual GPU deployment; more excluded model calls did not automatically reduce total time |
| Exact serialized-input cache | Under fixed token-length buckets, batch64 and padded final batches, reuse byte-identical ordered pair inputs within the same checkpoint/tokenizer/runtime namespace | 60 timed conditions, byte-identical cache/no-cache scores, decisions and rankings within the same computation setting |
| Engineering parsing memo | Reuse exact pure-function parsing intermediates with an empty cache per repeat | 30 actual conditions; identical model-call counts and outputs. Separate from serialized-input cache |
| Robust BGE LoRA | `full_control`, `drop_meta_p50_one_side`, `description_unit`; three epochs per scheme, one seed 20261005 | Nine local adapters; selected control/drop-meta epoch3, description/unit epoch2. No three-seed repeat claim |
| Router search | 115 validation-frozen policies, including validation query-group cross-validation | Complete retrospective score replay; configurations are not independent trained models |
| Lightweight models | 27 feature models + 18 no-identifier variants; 12 classification heads over frozen BGE embeddings | Train/validation exploration and retained unfavorable held-out results; no universal superiority |
| GPT blind judgments | Full-pool, selective, expanded, and challenge600 Codex independent-agent workflows | Real judgments; one workflow may be shared across scorer seeds. No billed API latency/cost |

Robust LoRA uses rank16, alpha32, dropout0.05, learning rate0.0001, train batch12, validation batch64, maximum length256, and symmetric augmentation. Random metadata masking removes category/specifications from one side with probability0.5 during training; inference restores original fields. Both new validation selectors choose the same epoch and threshold in each scheme. Their joint threshold/checkpoint selection is explicitly different from the old hard-refined protocol.

## Reference quality, reproducibility, and honest scope

- **Main benchmark:** original human reference and frozen splits. The existing test has been examined repeatedly; new analyses are retrospective.
- **Challenge600:** current construction-intent labels support exploratory comparison; independent double-human annotation and adjudication remain pending. It is a pair-only set without formal query candidate pools, so no Top3 claim is defined.
- **Alberta:** 135 unique bid queries against 501 catalog items yield 67,635 pairs. The 2024/2026 pools are paired year views, not 270 independent queries. Later comparisons use a frozen AI reference with 56 uncertain pairs; human gold remains pending. Uncertain rows retain their actual ranking slots and are excluded from known-reference quality denominators only after ranking.
- **Timing:** resident, synchronized batch processing includes the gates, serialization, tokenization, GPU inference, thresholding and ranking as defined per experiment. It excludes candidate retrieval, loading, file import and human review. Timing inputs may include audit queries. The 2.88 CNY/hour estimate is proportional GPU rental amortization, not a billed API price or complete deployment bill.
- **Model availability:** original BGE/Qwen trained checkpoint paths are recorded in server manifests, but those weights are not locally packaged in this dataset release. Locally available robust adapters and historical MiniLM checkpoints require a future explicit weight release and base-model instructions.
- **Code portability:** several original scripts and frozen plans contain machine-specific paths and hashes. Preserve their original evidence; provide portable launchers and configurable paths in a later code release. A documented method is not a verified clean-install reproduction.
- **Pending work:** a new untouched WSDOT expansion, final human gold for Alberta/challenge600, billed GPT API benchmarking, fresh selective 19-query/54-pair GPT judgments, and independent repeated seeds for new LoRA remain incomplete.

Failure cases, lower-scoring methods, batch-shape numerical drift, and the distinction between pair acceptance and actual Top3 are retained in the source evidence. The current results support limited method comparisons and measured throughput improvements; they do not establish one method as best across all datasets, metrics, costs, or future inputs.

## Authoritative source hierarchy

`output/router_research_20261005/final_review_delivery` and its underlying experiment folders contain the latest full comparison and independent checks. `output/router_research_20261005/all_experiment_tables/method_family_inventory.json` maps 38 distinct families; copied delivery tables, partial outputs superseded by full outputs, synthetic QA fixtures and repeated archives are not additional experiments.

`output/paper_experiment_completion_20261005/audit/experiment_completion_matrix.csv` records the earlier completion audit and remaining requirements. Its Alberta/600 inference-only status predates the later AI/construction-reference comparisons; it must not erase their continuing lack of human gold. The accompanying `paper/main.tex` is an English increment based on the user-designated original paper, preserves the older benchmark tables, and predates the later router/cache/LoRA delivery. It is not a manuscript already updated with all latest experiments.
