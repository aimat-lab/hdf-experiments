"""
figure_bo -- Bayesian optimization sample efficiency (demo of main-text Figure 5a,b).

Normalized regret of the best molecule found so far (lower is better) versus BO
round for the ClogP objective (target value 15 on AqSolDB), one panel per
embedding size: random search, Morgan fingerprints with a Tanimoto kernel and
HDF with a linear kernel (the surrogates of Figure 5), plus the two SI
surrogates (Morgan PCA + Matern, HDF + Matern) as thin lines. Lines are the mean
over the campaigns, bands the standard error.

Data: the campaign results of ``bo_benchmark.py`` under $EX24_ROOT/runs (the
reproducible run sets EX24_ROOT to ``_ex24_demo``). The paper's figure
(100 campaigns, nine sizes, QED as well) is made by ``make_figure_bo.py`` from
the full benchmark (protocols/ex_24.txt).

Usage::

    EX24_ROOT=_ex24_demo python demo_figure_bo.py
"""
import json
import os
import pathlib
import re

import numpy as np
import matplotlib.pyplot as plt

from figure_style import apply_style, COLOR_HDC, COLOR_FP, COLOR_RANDOM, save_figure

PATH = str(pathlib.Path(__file__).parent.absolute())
ROOT = os.environ.get('EX24_ROOT', os.path.join(PATH, '_ex24_demo'))
FIG_DIR = os.path.join(PATH, 'figures')
OBJECTIVE = 'clogp'

# (method, label, colour, line width): Figure 5 surrogates bold, SI surrogates thin
METHODS = [
    ('random', 'Random search', COLOR_RANDOM, 2.0),
    ('morgan_pca', 'Morgan PCA + Matérn (SI)', '#4C64EB', 1.0),
    ('hdf_matern', 'HDF + Matérn (SI)', '#69F7AE', 1.0),
    ('morgan_tanimoto', 'Morgan + Tanimoto', '#7C92FF', 2.4),
    ('hdf_linear', 'HDF + linear (ours)', COLOR_HDC, 2.4),
]

apply_style()


def regret_curves(method: str, size) -> np.ndarray:
    """Normalized regret per round of all finished campaigns of one cell, shape (campaigns, rounds + 1)."""
    folder = os.path.join(ROOT, 'runs', OBJECTIVE, method, 'Dna' if size is None else f'D{int(size)}')
    if not os.path.isdir(folder):
        return np.empty((0, 0))
    curves = []
    for name in sorted(n for n in os.listdir(folder) if re.fullmatch(r'c\d+\.npz', n)):
        result = np.load(os.path.join(folder, name))
        meta = json.loads(str(result['meta']))
        curves.append((meta['objective_max'] - result['best']) / (meta['objective_max'] - meta['objective_min']))
    return np.array(curves)


def main():
    folder = os.path.join(ROOT, 'runs', OBJECTIVE)
    if not os.path.isdir(folder):
        raise SystemExit(f'No BO campaigns found under {folder}.')
    sizes = sorted({int(d[1:]) for m in os.listdir(folder) for d in os.listdir(os.path.join(folder, m))
                    if re.fullmatch(r'D\d+', d)})
    if not sizes:
        raise SystemExit(f'No BO campaigns with an embedding size under {folder}.')

    fig, axes = plt.subplots(1, len(sizes), figsize=(6.4 * len(sizes), 4.6), squeeze=False)
    for ax, size in zip(axes[0], sizes):
        for method, label, color, lw in METHODS:
            curves = regret_curves(method, None if method == 'random' else size)
            if curves.size == 0:
                continue
            rounds = np.arange(curves.shape[1])
            mean = curves.mean(axis=0)
            sem = curves.std(axis=0, ddof=1) / np.sqrt(len(curves)) if len(curves) > 1 else np.zeros_like(mean)
            ax.plot(rounds, mean, color=color, lw=lw, label=f'{label} (n={len(curves)})', zorder=3)
            ax.fill_between(rounds, mean - sem, mean + sem, color=color, alpha=0.15, lw=0, zorder=2)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.set_xlabel('BO round')
        ax.set_ylabel(r'Normalized regret  $\downarrow$')
        ax.set_title(f'ClogP target on AqSolDB, {size} dimensions')
        ax.legend(loc='upper right', fontsize=9)

    fig.tight_layout()
    save_figure(fig, FIG_DIR, 'figure_bo')


if __name__ == '__main__':
    main()
