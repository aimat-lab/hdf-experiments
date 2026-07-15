# Hyperdimensional Fingerprints — experiment artifact

Reproducibility artifact for the paper **"Hyperdimensional Fingerprints (HDF):
training-free molecular representations"**.

HDF replaces the *learned* transformations of a message-passing graph neural
network with fixed **algebraic operations on high-dimensional vectors**, yielding
a deterministic molecular fingerprint that requires **no training**. This
repository contains the hyperdimensional-computing library (`graph_hdc`) and the
experiment code that produces the paper's results.

> The HDF **method** is separately archived as a Python package at
> [`doi.org/10.5281/zenodo.19373621`](https://doi.org/10.5281/zenodo.19373621).
> This repository is the accompanying **experiment code** and is structured as a
> [Code Ocean](https://codeocean.com) compute capsule.

## Layout

```
environment/     Dockerfile + postInstall — the pinned, rebuildable environment
code/
  graph_hdc/     the HDC library (encoders, HyperNet, binding, decoding)
  experiments/   the paper's experiment scripts (PyComex) + YAML configs
  tests/         pytest suite for the library
  run            reproducible-run entry point (scaled-down demo by default)
  collect_outputs.py   gathers metrics + figures into the results folder
data/            datasets (fetched on demand via chem-mat-database; not committed)
metadata/        Code Ocean capsule metadata
requirements.txt pinned third-party dependencies (Python 3.11)
```

## What it reproduces

| Paper item | Experiment | Config family |
|---|---|---|
| Fig. 1 — model comparison | property prediction across GB/KNN/RF/NN | `predict_molecules__{hdc,fp}__*` |
| Table 1 — fingerprint comparison | NN across datasets | `predict_molecules__{hdc,fp}__*` |
| Fig. `size` — dimensionality ablation | MAE vs. embedding size | `predict_molecules` (size sweep) |
| Fig. `ged` a — GED correlation | representation distance vs. graph edit distance | `molecule_similarity__{hdc,fp}__*` |
| Fig. `ged` b — KNN error ratio | nearest-neighbor accuracy | `predict_molecules` / bioactivity |
| Fig. `bo` — Bayesian optimization | ClogP / QED targeting | `optimize_molecule_bo__{hdc,fp,random}__*` |
| Suppl. — virtual screening | similarity-based bioactivity ranking | `predict_bioactivity__{hdc,fp}__*` |

## Running

### On Code Ocean
Create a capsule (**New Capsule → Clone from Git**, then switch to this repo),
open **Reproducible Run**. The `run` script executes and writes a metrics
summary and figures to `/results`.

### Locally with Docker
```bash
docker build -t hdf-artifact -f environment/Dockerfile .
mkdir -p out
docker run --rm -v "$PWD/code":/code -v "$PWD/out":/results \
    -e TIER=demo -w /code hdf-artifact bash run
# browse out/summary.md and out/figures/
```

### Locally with a virtualenv
```bash
pip install -r requirements.txt
pip install "chem_mat_database @ git+https://github.com/the16thpythonist/chem_mat_data.git"
cd code && TIER=smoke RESULTS_DIR=./out bash run
```

## Demo vs. full reproduction

The `run` driver has three tiers (`TIER=smoke|demo|full`):

- **`demo` (default)** — small datasets, subsampled to a few thousand molecules,
  3 seeds, reduced BO trials. Produces representative versions of every figure in
  a few hours on a laptop-class CPU. Intended to demonstrate that the pipeline
  works end to end.
- **`full`** — the exact paper protocol: all 9 datasets, full embedding sweeps,
  5 seeds (0–4), 25 BO trials, 50 screening repetitions. This requires a
  **multi-core cluster** and network access to download the large datasets
  (`qm9_smiles` ≈ 670 MB, `zinc250k`, `compas_3x`) and is **not** feasible within
  Code Ocean's default compute budget.

## Data

All datasets are public and fetched by identifier through the
[`chem-mat-database`](https://github.com/the16thpythonist/chem_mat_data) package
(no data is committed here). During the environment build (which has network),
`environment/postInstall` warms the cache for the small demo datasets; the large
datasets download on demand when a `full` run needs them.

## Tests

```bash
cd code && pytest -q -m "not localonly"
```

## License

MIT — see [`LICENSE`](LICENSE).
