# Hyper-Dimensional Fingerprints as Molecular Representations — experiment capsule

Reproducibility capsule for the paper **"Hyper-Dimensional Fingerprints as
Molecular Representations"** (Teufel, Torresi, Eberhard, Friederich; revised
version for Nature Communications, NCOMMS-26-058162; preprint arXiv:2604.27810).

Hyper-dimensional fingerprints (HDF) replace the *learned* transformations of a
message-passing graph neural network with fixed **algebraic operations on
high-dimensional vectors**, yielding a deterministic molecular fingerprint that
requires **no training**. This repository contains the hyperdimensional-computing
library (`graph_hdc`) and the experiment code behind the results of the revised
paper and its Supplementary Information.

> The HDF **method** is separately archived as a Python package at
> [`doi.org/10.5281/zenodo.19373621`](https://doi.org/10.5281/zenodo.19373621)
> (`hyper_fingerprints`, unit-modulus codebooks since version 0.5.1). This
> repository is the accompanying **experiment code**, structured as a
> [Code Ocean](https://codeocean.com) compute capsule.

## The standard HDF configuration

All HDF results of the revised paper use one standard encoder, which is the
default of the library and of every experiment module here:

| Setting | Value | Parameter (experiment modules) |
|---|---|---|
| Message passing | along both directions of every bond | `BIDIRECTIONAL=True` |
| Codebooks (element vectors, fractional power encoders) | unit-modulus Fourier spectra (FHRR) | `SPECTRUM='unit'` |
| Hydrogen count of an atom | all bonded hydrogens (RDKit `GetTotalNumHs`) | `HYDROGEN_COUNT='total'` |
| Graph attributes | graph size and diameter encoded and bound to the readout | `GRAPH_ATTRIBUTES=True` |
| Dimension, depth | D = 2048, L = 2 (unless an experiment sweeps them) | `EMBEDDING_SIZE`, `NUM_LAYERS` |

The original submission used one-directional message passing, Gaussian
codebooks and implicit hydrogen counts; the old values remain selectable for
comparison (`BIDIRECTIONAL=False`, `SPECTRUM='gaussian'`, `HYDROGEN_COUNT='implicit'`).
`code/tests/test_unit_modulus.py`, `test_hypernet_bidirectional.py` and
`test_hydrogen_count.py` check these defaults.

## Layout

```
environment/     Dockerfile + postInstall: the pinned, rebuildable environment
code/
  graph_hdc/     the HDC library (encoders, HyperNet, baselines, BO, decoding)
  experiments/fingerprints/
                 experiment modules (PyComex) + YAML configs, analysis scripts
                 (analyze_ex_NN.py), paper figure/table scripts (make_*.py),
                 demo figure scripts (demo_figure_*.py)
  protocols/     ex_NN.txt: the exact command lines behind every paper item
  run_protocol.py  runs (parts of) a protocol file
  run            reproducible-run entry point (scaled-down demo by default)
  collect_outputs.py   gathers metrics + figures into the results folder
  tests/         pytest suite (library, baselines, protocol files)
data/            external data (see data/README.md); datasets are fetched on demand
metadata/        Code Ocean capsule metadata
requirements.txt pinned third-party dependencies
```

The library and the experiment modules are a copy of the development
repository `graph_hdc` (branch `revision/consolidated`, commit `f303c51`).

## What it reproduces

Each paper item maps to one experiment (`ex_NN`) with a protocol file in
`code/protocols/`. The header of every protocol file states the paper items,
the number of runs, the analysis commands, the compute cost of the paper's
runs and the data needed. Main-text Figure 1 is the method overview (no code).

| Paper item | Experiment | Protocol | Modules | Analysis / figure |
|---|---|---|---|---|
| **Table 1** (MLP), **Table S6** (KNN), **Tables S7, S8** (tuned MLP, selected configurations; search space Table S4) | ex_27 | `ex_27.txt` | `predict_molecules__{hdc,fp}.py`, `_optuna_ex_27.py` | `analyze_ex_27.py fixed` / `opt` |
| **Fig. 2** model comparison (GB, KNN, RF, NN; fixed + tuned; Section S5.1, Tables S3, S5) | ex_28 (+ ex_27) | `ex_28.txt` | `predict_molecules__{hdc,fp}.py`, `_optuna_ex_28.py` | `analyze_ex_28.py`, `make_figure_model_comparison.py` |
| **Fig. 3a** edit-based GED correlation (Section S9.1) | ex_08_c | `ex_08_c.txt` | `molecule_similarity__{hdc,fp}.py` | `analyze_ex_08c.py`, `make_figures_ged_edit.py` |
| **Fig. 3b** KNN error ratio, **Fig. 4** embedding-size ablation (Section S5.3), **Fig. S1** training-set size | ex_29 | `ex_29.txt` | `predict_molecules__{hdc,fp}.py` | `analyze_ex_29.py`, `make_figure_knn_ratio.py`, `make_figure_size.py`, `make_figure_training_size.py` |
| **Fig. 5** Bayesian optimization; **Section S7, Fig. S3** (all objectives and surrogates), **Tables S17, S18** | ex_24 | `ex_24.txt` | `bo_benchmark.py`, `graph_hdc/bo.py` | `analyze_ex_24.py`, `make_figure_bo.py` |
| **Fig. S4** BO wall-clock time (original benchmark) | ex_07_g | `ex_07_g.txt` | `optimize_molecule_bo__{hdc,fp,random}.py` | `make_figure_bo_wallclock.py` |
| **Section S6.2, Fig. S2a** virtual screening | ex_11_b | `ex_11_b.txt` | `predict_bioactivity__{hdc,fp}.py` | `analyze_ex_11b.py`, `make_figure_ged.py` |
| **Section S6.3, Table S9** contribution of the graph size/diameter descriptors | ex_25 (+ ex_14, ex_19) | `ex_25.txt` | `predict_molecules__{hdc,fp}.py` | `analyze_ex_25.py` |
| **Section S8, Fig. S5** bit depth | ex_20 | `ex_20.txt` | `predict_molecules__hdc.py` (`QUANTIZE_BITS`) | `analyze_ex_20.py` |
| **Section S9.2, Fig. S6, Fig. S2b** exact graph edit distance | ex_17 (+ ex_22 arms) | `ex_17.txt` | `ged_exact_pairs.py`, `ged_exact_correlation.py` | `analyze_ex_22_ged.py`, `make_figure_ged_balanced_subset.py`, `make_figure_ged.py` |
| **Section S10, Table S10** comparison with GNNs (hyperparameters Table S15) | ex_14 | `ex_14.txt` | `predict_molecules__{hdc,gnn,gnn_random}.py` | `analyze_ex_14.py` |
| **Section S11, Table S11** modern fingerprints: SECFP, MAP4, Sort & Slice, Sherlock (Table S16) | ex_19 (+ ex_14) | `ex_19.txt` | `predict_molecules__{fp,sherlock}.py` | `analyze_ex_19.py` |
| **Section S12, Fig. S7, Table S12** recovery of the atom composition | ex_23 | `ex_23.txt` | `decode_composition.py`, `graph_hdc/special/composition.py` | `analyze_ex_23.py` |
| **Section S13, Tables S13, S14** stereochemistry | ex_21u | `ex_21u.txt` | `molecule_collisions.py`, `predict_enantiomers__{hdc,fp}.py`, `predict_molecules__{hdc,fp}.py` | `analyze_ex_21.py` |
| 1-WL collisions (Methods, expressivity; response to R3.2) | ex_16 | `ex_16.txt` | `molecule_collisions.py` | `analyze_ex_16.py` |
| Crippen logP as a further graph attribute (response letter only) | ex_26 (+ ex_14) | `ex_26.txt` | `predict_molecules__hdc.py` (`GRAPH_CLOGP`) | `analyze_ex_26.py` |

**Seeds and repetitions, as in the revised paper.** Table 1, Tables S6/S7,
Figs. 2–4 and Fig. S1: 10 seeds (0–9; split and network; Table 1, S6, S7 and
Fig. 2 with one fixed HDF codebook, Figs. 3b, 4 and S1 with a new codebook per
seed). Tables S9–S11, S13, S14 and Fig. S5: 10 seeds. Bayesian optimization
(Fig. 5, Fig. S3): 100 campaigns per objective, representation and size; Fig. 5
shows HDF with a **linear kernel** against Morgan fingerprints with a
**Tanimoto kernel** (and random search), Fig. S3 adds HDF and Morgan-PCA with a
Matérn-5/2 kernel as controls. Virtual screening: 50 repetitions of 5 query
actives. Exact GED: 5 HDF codebook seeds.

Some protocols depend on others: ex_19, ex_25 and ex_26 read the ex_14 HDF
archives and splits, and ex_28 reads the ex_27 archives. Run them in the same
`experiments/fingerprints` folder (the shared `.cache` gives identical splits).

## Running

### The Reproducible Run (`code/run`)

On Code Ocean, **Reproducible Run** executes `code/run`. It runs a scaled-down
version of the main experiments with the revised HDF and the revised protocols
and writes a metrics summary, logs and figures to `/results`:

1. **Table 1 / Table S6 protocol**: the MLP (100,100) and the KNN (k = 5,
   cosine distance for HDF, Tanimoto for Morgan) trained on the same splits, one
   fixed HDF codebook, **10 seeds**, HDF vs Morgan (radius 2, 2048 bits) on BACE,
   Lipophilicity, AqSolDB and ClogP (full datasets). Figure `figure_prediction`.
2. **Fig. S5**: the bit-depth ablation, the paper's exact runs on FreeSolv
   (10 seeds x 7 runs from `protocols/ex_20.txt`). Figure `figure_bits`.
3. **Fig. 3a analogue**: edit-based GED correlation at D = 32–2048 on a QM9
   subsample (25 seed molecules; the paper uses 100 ZINC250k seeds, which needs
   about 28 GB of RAM at D = 2048). Figure `figure_ged`.
4. **Fig. 5a,b analogue**: the paper's BO benchmark code on the ClogP objective
   (AqSolDB) at 16 and 1024 dimensions, with **10 campaigns** per method instead
   of 100: HDF + linear kernel, Morgan + Tanimoto, random search, and the two SI
   surrogates. Figure `figure_bo`.

Tiers (`TIER=smoke|demo|full`): `smoke` (minutes; 1 seed, BACE only, 2 BO
campaigns), `demo` (default; about 1–1.5 h with 4 CPU cores), `full` (the full
protocols ex_27, ex_20, ex_08_c and ex_24; needs a cluster). `JOBS` sets the
number of parallel runs (default: half the cores, at most 8).

### Full protocols (`code/run_protocol.py`)

Every protocol file runs stage by stage (warmup and primer runs that write
shared caches first), with the lines of a stage in parallel:

```bash
cd code
python run_protocol.py ex_27 --list                       # header, stages, number of runs
python run_protocol.py ex_27 --stage warmup_fixed --stage fixed --jobs 8
python run_protocol.py ex_14 --grep freesolv --set EPOCHS=5 --dry-run   # a subset, with an override
cd experiments/fingerprints && python analyze_ex_27.py fixed
```

Without a GPU (or with `--cpu`), the device parameters of the paper's GPU runs
are switched to the CPU. The paper ran the large protocols on HPC clusters; the
protocol headers give their cost, from a few CPU hours (ex_16, ex_20, ex_23) to
thousands of CPU/GPU hours (the trained GNNs of ex_14, ex_24, ex_27/ex_28 on QM9
and COMPAS-3X). Results land in `code/experiments/fingerprints/results/`
(PyComex archives) and in the `_exNN/` folders of the analysis scripts.

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
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.9.1
pip install -r requirements.txt
pip install --no-deps mhfp==1.9.6
pip install "chem_mat_database @ git+https://github.com/the16thpythonist/chem_mat_data.git"
pip install "vgd_counterfactuals @ git+https://github.com/the16thpythonist/vgd_counterfactuals.git"
cd code && TIER=smoke RESULTS_DIR=./out bash run
```

## System requirements

- **Operating system:** Linux (tested on Ubuntu 22.04). The Docker image runs on
  any host with a Docker engine; the virtualenv path works on Linux/macOS with
  Python 3.11 or 3.12.
- **Python:** 3.11 (development) or 3.12 (the Code Ocean base image). All
  third-party versions are pinned in `requirements.txt` and in
  `environment/Dockerfile`.
- **Hardware:** no non-standard hardware. The environment installs the **CPU
  build** of PyTorch; the reproducible run needs no GPU and about 8 GB of RAM.
  The full protocols need a multi-core cluster; several used GPUs in the paper
  (the MLPs of ex_27/ex_28/ex_29, the GNNs of ex_14, the BO acquisition on
  ZINC250k), which only changes their run time.
- **Typical install time:** building the Docker image takes about 15–30 min
  (PyTorch, RDKit and the other scientific wheels); the virtualenv install about
  5–10 min.

## Data

All molecular datasets are public and fetched by identifier through
[`chem-mat-database`](https://github.com/the16thpythonist/chem_mat_data) (nothing
is committed). `environment/postInstall` warms the cache for the datasets of the
reproducible run during the environment build; the large datasets (QM9,
ZINC250k, COMPAS-3X, the virtual-screening benchmarks) download on first use.
The stereochemistry protocol (ex_21u) also needs two external files, which its
`prepare` stage downloads (see `data/README.md`).

## Tests

```bash
cd code && pytest -q -m "not localonly"
```

`tests/test_protocols.py` checks that every protocol line calls an existing
script with parameters that the experiment module defines. 25 older tests of the
graph-reconstruction part of the library (`test_reconstruct.py`,
`test_special_molecules.py`, `test_models.py`, `test_binding.py`,
`test_composite_hypernet*.py`) fail in the development repository as well; they
cover code that the paper does not use.

## License

MIT — see [`LICENSE`](LICENSE).
