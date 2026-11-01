# emoji-opt-lab

`carpedm20/emoji` 是一个把 Unicode 表情符号与 `:shortcode:` 互转的 Python 库。本实验在它的
核心分词器 `emoji/tokenizer.py` 做了**两处协同改动**（`ignore` 列表→集合 + 纯文本连续段批量快路径），
使 `demojize()` 中位加速 **1.22x**，并在 2028 组差分用例上逐字节一致。

Upstream: https://github.com/carpedm20/emoji

## 加速比

| 规模 | 基线中位数 (ms) | 优化后中位数 (ms) | 加速比 |
| --- | --- | --- | --- |
| small (3077 字符) | 2.396 | 1.980 | 1.21x |
| medium (8026 字符) | 6.290 | 5.076 | 1.24x |
| large (18102 字符) | 14.130 | 11.570 | 1.22x |

三个规模的中位加速比 **1.22x**（≥1.15x 闸门通过）。

## 差分一致性与闸门

差分测试 `tests/test_diff.py` 对 **2028 组输入**（随机 + 边界：空串、单字符、极值、
非 ASCII、长输入、ZWJ 序列、变化选择符 `\ufe0e/\ufe0f`），逐字节比对 `demojize`、`tokenize`、
`analyze`、`emoji_list` 的输出，**0 差异**。

| 闸门 | 判定 | 结果 | 复现命令 |
| --- | --- | --- | --- |
| G1 上游测试全绿 | 0 failed | ✅ 102 passed | `PYTHONPATH=.:utils python -m pytest tests_upstream -q` |
| G2 差分一致 | 0 差异 | ✅ 2028 cases, 0 diffs | `python tests/test_diff.py` |
| G3 中位加速 | ≥1.15x | ✅ 1.22x | `python benchmark/bench.py . optimized large x.json` |
| G4 大规模不退化 | ≥0.95x | ✅ large 1.22x | 同上 large 规模 ×2 样本 |
| G5 内存不变差 | ≤1.10x | ✅ 21000/20812 = 1.009 | `/usr/bin/time -v python benchmark/bench.py ...` |

## 复现

本仓库自带优化的 `emoji/`（根目录）与基线 `base/` 两份源码，以及上游测试 `tests_upstream/` 和 `utils/`，
无需联网 clone 上游。三条命令：

```bash
python -m pytest tests_upstream -q          # G1: 102 passed
python tests/test_diff.py                    # G2: 2028 cases, 0 diffs
python benchmark/bench.py . optimized large benchmark/raw/smoke.json   # G3/G4: bench one scale
```

跑 G1 时需要把 `utils/` 放进 `PYTHONPATH`：
`PYTHONPATH=.:utils python -m pytest tests_upstream -q`（等价）。

## 本轮创新

首次把 emoji 分词器的 `ignore` 下标检查从 O(n) 列表改为 **O(1) 集合**（消除宽输入上的
二次方尾巴），并同时加一条**纯文本连续段批量快路径**（一次 `yield from` 刷出整段单字符
`Token`，而不是每个字符都清空重建 `result` 列表）。这不是单行换皮：它是同一个热循环里的
两处协同改动，`patch.diff` 只动 `emoji/tokenizer.py` 一个文件（+22/−4，≤80 行），且不改公共
API 语义，2028 组差分逐字节一致。台账里多解释器交叉测量因本机只有 Python 3.12 而取消，
改为把「宽输入无退化」作为稳定性证据。

## 环境

- CPU: AMD EPYC 7K62 48-Core（qemu KVM，4 vCPU）
- 内存: 3723 MB
- 运行时: Python 3.12.3 / node v24.19.0（未改）
- 种子: 12345（`demo_cc` / bench 固定）
- 上游提交: d5d59d591f8590ada989f0bdf31603b3fe84e103（2026-09-16）

## 溯源

`patch.diff` 基于上游 `carpedm20/emoji` 提交 `d5d59d591f8590ada989f0bdf31603b3fe84e103`，
只改 `emoji/tokenizer.py`。LICENSE 沿用上游 New BSD（见 LICENSE）并注明来源与本轮改动范围。