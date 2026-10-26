# data/

This directory is intentionally (almost) empty.

All molecular datasets used in this work are **public** and are fetched on demand
by their identifier through the
[`chem-mat-database`](https://github.com/the16thpythonist/chem_mat_data) Python
package — nothing is committed to this repository. The identifiers used are:

| Identifier | Molecules | Property |
|---|---|---|
| `hopv15_exp` | 175 | PCE, V_oc |
| `freesolv` | 639 | ΔG hydration |
| `bace_reg` | 1,513 | IC50 |
| `lipophilicity` | 4,199 | logD |
| `aqsoldb` | 9,889 | logS |
| `aqsoldb` (+ RDKit Crippen) | 9,887 | ClogP |
| `compas_3x` | 39,482 | U_0, Gap, μ |
| `qm9_smiles` | 133,882 | μ, C_v, ZPVE, α, ΔH, U_0, Gap |
| `zinc250k` | 249,455 | QED, ClogP |
| `beet`, `open_melting_point` | | BO objectives (honey-bee LD50, melting point; ex_24) |
| `riniker_1`, `riniker_2`, `muv`, `dud_e` | | virtual-screening benchmarks (ex_11_b) |

The stereochemistry protocol (`code/protocols/ex_21u.txt`) needs two further
public files, which its `prepare` stage downloads into this folder:

- `data/chiro_docking/chiro_docking.csv`, written by
  `prepare_chiro_docking.py` from the docking-score splits of Adams et al.
  (ChIRo, ICLR 2022; figshare);
- `data/cmrt_elution/cmrt_adh.csv`, written by `prepare_cmrt_elution.py` from
  the CMRT subset of Baimacheva et al. (GitHub `jairesdesousa/chiraldlsv`).

On Code Ocean, `/data` is read-only during a run: run the two `prepare` scripts
once in a Cloud Workstation and keep the CSVs in the capsule's data folder, or
pass other paths (`PAIRS_CSV`, `CHIRO_CSV`).

During the environment build (`environment/postInstall`) the cache is warmed for
the small datasets used by the default `demo` run. Larger datasets download the
first time a `full` run requests them (requires network access).
