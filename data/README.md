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

During the environment build (`environment/postInstall`) the cache is warmed for
the small datasets used by the default `demo` run. Larger datasets download the
first time a `full` run requests them (requires network access).
