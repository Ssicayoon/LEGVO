# Reproducing Evaluation Results

All commands run from `/path/to/LEGVO` with `PYTHONPATH=src`.

## Prerequisites

```bash
git clone --recursive https://github.com/Ssicayoon/LEGVO.git
cd LEGVO
pip install -e .
cd egglog-experimental && cargo build --release && cd ..
```

## Table 2: Overall Results (TP/TN/FP/FN, Precision, Recall)

```bash
bash scripts/verify_accuracy.sh
```

Output: `TP=17009 TN=9236 FP=51 FN=2504`, Recall=87.2%, Precision=99.7%

Note: `verify_accuracy.sh` runs the full pipeline (primary + finalization passes). For primary-pass-only results, use `run_phase12_per_transform.py` below.

## Table 3: Baseline Comparison

### PET/isl

```bash
PYTHONPATH=src python3 scripts/run_baseline_pet.py
```

Output: Parseable=70.5%, Precision=97.0%, Recall=86.9%, FP=532

### Alive2

```bash
PYTHONPATH=src python3 scripts/run_baseline_alive2.py
```

Output: Parseable=69.0%, Precision=98.8%, Recall=54.5%, FP=134

## Figure: Baseline Comparison (per-category recall)

Data from the same baseline scripts above. Per-category results:

| Tool | Expression | Loop | Statement | Syntactic |
|------|-----------|------|-----------|-----------|
| PET/isl | 97.9% | 87.2% | 25.7% | 96.9% |
| Alive2 | 37.5% | 43.5% | 36.8% | 89.4% |
| LEGVO | 98.2% | 52.9% | 84.8% | 99.9% |

Generate figure:
```bash
cd plots && python3 draw_baseline_comparison.py
```

## Table 4: Per-Category Recall

```bash
PYTHONPATH=src python3 scripts/run_phase12_per_transform.py
```

Output includes per-category and per-transform recall for all 32 types (primary + finalization passes).

## Figure: Per-Transform Recall + SwapDB/DbShift Ablation

### Panel (b): All 32 transforms

Data from `run_phase12_per_transform.py` above.

### Panel (a): Polyhedral-gated structural transforms (w/ vs w/o SwapDB/DbShift)

```bash
PYTHONPATH=src python3 scripts/run_ablation_interchange.py
```

Output:
| Transform | w/ SwapDB+Polyhedral | w/o | Delta |
|-----------|-----------------|-----|-------|
| fission | 72.9% | 15.8% | +57.1% |
| init_hoist | 66.4% | 29.3% | +37.1% |
| fusion | 64.1% | 31.4% | +32.7% |
| interchange | 53.6% | 46.7% | +6.9% |

Generate figure:
```bash
cd plots && python3 draw_per_transform_recall.py
```

## Figure: Cumulative Ablation

```bash
PYTHONPATH=src python3 scripts/run_ablation.py
```

Output (cumulative, each row removes one more component):
| Configuration | Recall |
|--------------|--------|
| Full LEGVO | 87.2% |
| − Finalization norm. | 86.8% |
| − Polyhedral + SwapDB/DbShift | 83.9% |
| − Algebraic rules | 68.8% |
| − Normalization | 41.4% |

Generate figure:
```bash
cd plots && python3 draw_ablation.py
```

## Table 6: Timing Breakdown

```bash
PYTHONPATH=src python3 scripts/run_timing_breakdown.py
```

Output (500 random samples):
| Stage | Median | P95 | P99 | Max |
|-------|--------|-----|-----|-----|
| Parse + Normalize | 0.04s | 0.05s | 0.11s | 0.16s |
| Polyhedral (PET/isl) | <0.01s | 0.67s | 2.02s | 8.0s |
| Egglog saturation | <0.01s | 0.10s | 1.60s | 3.7s |
| Total | 0.04s | 0.83s | 4.15s | 8.1s |

## Regenerating All Figures

```bash
cd plots/
python3 draw_per_transform_recall.py
python3 draw_ablation.py
python3 draw_baseline_comparison.py
```

Figures are saved to `../9-Figures/*.pdf`.
