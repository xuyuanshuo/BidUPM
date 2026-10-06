# BidUPM

**Construction bid-item matching datasets and experimental evidence.**  
**工程招投标清单匹配：数据集、方法和实验复现资料。**

本仓库整理当前研究数据及独立的历史数据版本，包括 **Alberta 原始表格与全部
候选配对**。数据按来源、版本、用途和标注状态组织；保留标注依据、冻结记录、
字段说明和 SHA-256 校验值。数据快照日期：**2026-10-05**。

## 数据集

| 数据集 | 内容与规模 | 标签性质 |
|---|---|---|
| [BidUPM-12k](docs/DATASET_CARDS.md#bidupm12k) | 12,092 对；训练、验证、锁定测试、无参考和外部集合 | 人工审阅与裁决；初始建议列保留为历史 |
| [Alberta](docs/DATASET_CARDS.md#alberta) | 135 个查询；UPA 2024 的 237 项和 2026 的 264 项；合计 67,635 个候选配对 | 输入不含标签；另存 AI 参考标注及空白人工模板 |
| [困难诊断集](docs/DATASET_CARDS.md#challenge600) | 600 对，基于 300 个真实来源锚点构造 | 构造意图标签；人工标注尚未完成 |
| [历史 Alberta](docs/DATASET_CARDS.md#alberta_historical) | 2019–2026 UPA、跨年代码锚点和价格案例 | 代码规则及价格实验结果 |
| [历史数据版本](datasets/README.md) | 来源主集、价格案例、GPT55 扩展基准、历史人工确认集 | 分别记录人工、AI 和待标注状态 |
| [原始 NCDOT](docs/DATASET_CARDS.md#ncdot_raw) | 59,004 个清单记录、144,993 个价格记录；8,518,172 个规则生成配对 | 原始数据及规则标签 |
| [来源材料](docs/DATASET_CARDS.md#source_materials) | 原始招投标表、标准化记录及历史检索候选 | 来源与候选生成证据 |

完整文件清单：[datasets/manifest.json](datasets/manifest.json)。
下载包：[data_archives/](data_archives/README.md)。
字段与读取方法：[docs/DATA_FORMAT.md](docs/DATA_FORMAT.md)。

**Alberta 的 AI 参考标注和 600 对数据的构造标签不能称为独立人工金标准。**
历史版本与当前正式集合也不能直接合并后计算论文指标。

## 下载和还原

需要 Git 和 Python 3.10 或更高版本。数据工具仅使用 Python 标准库。

```sh
git clone https://github.com/xuyuanshuo/BidUPM.git
cd BidUPM
python scripts/materialize_datasets.py --restore-archives data_archives --restore-only
python scripts/verify_datasets.py
```

28 个独立 ZIP 完整保存打包后的数据目录，共约 281 MiB。还原程序先核对包及
每个文件的哈希，再恢复目录。较大的 CSV 保持 `.gz` 压缩；可按需解压，例如：

```sh
python scripts/materialize_datasets.py --dataset alberta --output-dir materialized
python scripts/materialize_datasets.py --dataset bidupm12k --output-dir materialized
```

大型原始配对 CSV 已保存在 11 个无损分片中；需要完整约 5 GB 的 CSV 时运行：

```sh
python scripts/materialize_datasets.py --dataset ncdot_raw/full_pairs --output-dir materialized
```

也可通过 GitHub 的 **Code → Download ZIP** 下载仓库，再运行相同命令。

## 方法与实验

[方法说明](docs/METHODS.md)记录传统基线、BGE/Qwen 适配与排序、验证器、规则优先
分流、缓存、补充集和 Alberta 迁移实验。[实验索引](experiments/EXPERIMENT_INDEX.csv)
标明各方法的完成状态和原始证据位置；[methods/](methods/README.md) 提供方法代码、
CPU 复核工具及复现条件；[experiments/](experiments/README.md) 保存实际实验资料。

评估须区分配对质量与实际至多三条返回结果。主评估采用 218 个查询；220 查询的
计时口径包含两个重分类审计池。阈值在验证集确定，测试集和 Alberta 不用于调参。
三组既有适配器 seed 与仅一个训练 seed 的新 LoRA 实验分别记录。

原始 BGE/Qwen 训练权重未在可访问的本地材料中找到，仓库明确列出这一复现条件；
保存的分数与结果可复核，重新运行神经模型仍需对应权重和模型运行环境。

## 来源、许可和引用

第三方原始数据的来源链接保留在各数据集的来源清单中。8 个 WSDOT 原始工作簿
未在本地找到，现有解析记录及来源链接已保留，缺失情况在数据说明中公开记录。

[LICENSE](LICENSE) 的 MIT 许可仅覆盖本次编写的 `scripts/` 数据工具。
数据及既有实验材料的权利状态见 [DATA_LICENSE.md](DATA_LICENSE.md)，本快照未设置
统一数据许可。引用本快照可使用 [CITATION.cff](CITATION.cff)，并保留原始来源归属。

## English quick start

This snapshot includes the adjudicated BidUPM benchmark, the Alberta bid form
and UPA catalogs, all current Alberta input representations, the controlled
600-pair diagnostic set, distinct historical datasets, and the raw NCDOT corpus.
Download the repository and run the restore and verification commands above.
Alberta references are AI-generated and provisional; challenge labels describe
construction intentions. Neither is an independently adjudicated human gold
standard. See the dataset cards and method documentation before comparing results.
