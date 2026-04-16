# LEGVO: Verifying LLM-Generated Loop Transformations via Binding-Aware Equality Saturation

LEGVO (**L**oop **E**quivalence via e-**G**raph **V**erification and p**O**lyhedral analysis) is a verification framework that automatically checks whether LLM-generated loop kernel optimizations preserve the semantics of the original program.

## Key Features

- **De Bruijn indexing**: Eliminates variable renaming differences by construction
- **Binding-aware e-graph constructors** (SwapDB/DbShift): Correctly adjust variable indices during structural loop transformations
- **Polyhedral-gated rules**: Uses PET/isl dependence analysis to gate structural rewrites
- **125 rewrite rules**: Algebraic, structural, binding-aware, and polyhedral-gated
- **Two-pass normalization**: Primary + finalization passes for robust canonicalization

## Quick Start

### Prerequisites

**Required:**
- Python 3.9+
- Rust toolchain (for building egglog)
- GCC (for compilation checks)
- PolyBench/C 4.2.1 ([download](https://web.cse.ohio-state.edu/~pouchet.2/software/polybench/))
- Python 3.13 with `islpy` and PET/tadashi (for polyhedral analysis)

**Optional (for baseline comparisons only):**
- Alive2 (`alive-tv`) and Clang (for Alive2 baseline)

### Build

```bash
# Clone with submodule
git clone --recursive https://github.com/Ssicayoon/LEGVO.git
cd LEGVO

# Build egglog engine
cd egglog-experimental && cargo build --release && cd ..

# Install LEGVO
pip install -e .

# Set PolyBench path
export PB_UTILS=/path/to/PolyBenchC-4.2.1/utilities
```

### Verify a single pair

```python
from pathlib import Path
from legvo.egraph.verify import verify

result = verify(
    Path("reference.c"),
    Path("candidate.c"),
    include_dirs=[Path("path/to/PolyBenchC-4.2.1/utilities")],
    mode="real",
)
print(result.status)   # "equivalent" or "unknown"
print(result.reason)   # human-readable explanation
```

### Run full evaluation

```bash
# Set PolyBench path
export PB_UTILS=/path/to/PolyBenchC-4.2.1/utilities

# Run main evaluation (28,800 samples, ~5 min with 20 workers)
bash scripts/verify_accuracy.sh

# Run ablation study
PYTHONPATH=src python3 scripts/run_ablation.py

# Run per-transform breakdown
PYTHONPATH=src python3 scripts/run_phase12_per_transform.py
```

See [docs/reproduce_eval.md](docs/reproduce_eval.md) for full reproduction instructions.

## Project Structure

```
LEGVO-release/
├── src/legvo/
│   ├── egraph/          # Core verification pipeline
│   │   ├── verify.py    # Main entry point
│   │   ├── extract.py   # C source → De Bruijn term
│   │   ├── normalize.py # Normalization passes
│   │   ├── rules.py     # 125 egglog rewrite rules
│   │   ├── term.py      # Term IR (De Bruijn indexed AST)
│   │   └── oracle.py    # Term-level polyhedral analysis
│   └── polyhedral/      # PET/isl polyhedral analysis
├── egglog-experimental/ # Extended egglog engine (git submodule)
├── scripts/             # Evaluation and baseline scripts
├── datasets/            # 28,800 LLM-generated variants
│   └── single_transform_full/
├── tests/               # Test suite
└── docs/                # Documentation
```

## Dataset

28,800 LLM-generated PolyBench/C variants:
- 30 kernels × 32 transformation types × 30 samples
- Ground truth via KernelBench execution comparison
- 19,513 correct (67.8%) + 9,287 incorrect (32.2%)

## Results

| Mode | Precision | Recall |
|------|-----------|--------|
| real (default) | 99.7% | 87.2% |
| fp_safe | 99.7% | 85.2% |

Median verification time: 0.04s per sample.

## License

MIT
