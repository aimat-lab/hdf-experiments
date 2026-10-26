"""
figure_bo -- Bayesian optimization sample efficiency.

Evolution of the objective (best distance-to-target found so far, lower is
better) versus optimization round, comparing a random-representation baseline,
Morgan fingerprints and hyperdimensional fingerprints (HDF) as the surrogate
model's molecular representation. Lines are the mean over independent trials,
shaded bands are +/- one standard deviation.

Data: ``optimize_molecule_bo__{hdc,fp,random}`` archives, reading the per-round
``bo_results.csv`` and the global optimum from ``experiment_data.json``.

Usage::

    python make_figure_bo.py
"""
import os
import json
import pathlib
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from figure_style import (apply_style, iter_archives, method_of, dataset_of,
                          METHOD_COLOR, METHOD_FILL, METHOD_LABEL, save_figure)

PATH = str(pathlib.Path(__file__).parent.absolute())
RESULTS_PATH = os.path.join(PATH, 'results')
FIG_DIR = os.path.join(PATH, 'figures')

DATASET_LABEL = {'clogp': 'ClogP', 'zinc250k': 'ZINC250k (QED)',
                 'freesolv': 'FreeSolv', 'qm9_gap': 'QM9 (gap)'}

apply_style()


def load_bo():
    """(dataset, method) -> {round -> [best_distance, ...]}, plus optimum per dataset."""
    curves = defaultdict(lambda: defaultdict(list))
    optimum = {}
    for path, namespace, meta, params in iter_archives(RESULTS_PATH):
        if 'optimize_molecule_bo' not in namespace:
            continue
        method = method_of(namespace)
        dataset = dataset_of(namespace)
        csv_path = os.path.join(path, 'bo_results.csv')
        if method == 'unknown' or not os.path.exists(csv_path):
            continue
        df = pd.read_csv(csv_path)
        for rnd, sub in df.groupby('round'):
            curves[(dataset, method)][int(rnd)].extend(
                sub['best_distance'].astype(float).tolist())
        # global optimum (best achievable distance) for the reference line
        dj = os.path.join(path, 'experiment_data.json')
        if dataset not in optimum and os.path.exists(dj):
            try:
                opt = json.load(open(dj)).get('optimization', {})
                if 'optimal_distance' in opt:
                    optimum[dataset] = float(opt['optimal_distance'])
            except Exception:
                pass
    return curves, optimum


def main():
    curves, optimum = load_bo()
    if not curves:
        raise SystemExit(f'No Bayesian-optimization archives found under {RESULTS_PATH}.')

    # pick the dataset with the most methods present (ties -> clogp if available)
    per_dataset = defaultdict(set)
    for (ds, m) in curves:
        per_dataset[ds].add(m)
    dataset = max(per_dataset, key=lambda d: (len(per_dataset[d]), d == 'clogp'))
    ds_label = DATASET_LABEL.get(dataset, dataset)
    print(f'BO figure dataset: {dataset}  methods: {sorted(per_dataset[dataset])}')

    fig, ax = plt.subplots(figsize=(7.6, 4.6))

    for method in ('random', 'fp', 'hdc'):     # draw HDF last so it sits on top
        rounds_map = curves.get((dataset, method))
        if not rounds_map:
            continue
        rounds = np.array(sorted(rounds_map))
        mean = np.array([np.mean(rounds_map[r]) for r in rounds])
        std = np.array([np.std(rounds_map[r]) for r in rounds])
        color = METHOD_COLOR[method]
        ax.fill_between(rounds, mean - std, mean + std, color=METHOD_FILL[method],
                        alpha=0.35, linewidth=0, zorder=2)
        ax.plot(rounds, mean, color=color, linewidth=2.4,
                label=METHOD_LABEL[method], zorder=3,
                solid_capstyle='round')

    if dataset in optimum:
        ax.axhline(optimum[dataset], color='#555555', linestyle='--', linewidth=1.2,
                   zorder=1, label=f'Global optimum ({optimum[dataset]:.2f})')

    ax.set_xlabel('BO round')
    ax.set_ylabel(r'Best distance to target found  $\downarrow$')
    ax.set_ylim(bottom=0)
    ax.set_xlim(left=0)
    ax.set_title(f'Bayesian optimization sample efficiency — {ds_label}')
    ax.legend(loc='upper right')

    fig.tight_layout()
    save_figure(fig, FIG_DIR, 'figure_bo')


if __name__ == '__main__':
    main()
