"""
figure_prediction -- Property prediction accuracy.

Grouped bars of the test-set coefficient of determination (R^2, higher is
better) of a neural-network regressor trained on Morgan fingerprints vs
hyperdimensional fingerprints (HDF), across molecular property datasets. Bars
show the mean over random seeds; error bars are +/- one standard deviation.

Data: ``predict_molecules__{fp,hdc}__*`` archives, reading
``metrics.test_neural_net.r2`` from ``experiment_data.json``.

Usage::

    python make_figure_prediction.py
"""
import os
import json
import pathlib
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from figure_style import (apply_style, iter_archives, method_of, dataset_of,
                          COLOR_FP, COLOR_HDC, COLOR_FP_FILL, COLOR_HDC_FILL,
                          save_figure)

PATH = str(pathlib.Path(__file__).parent.absolute())
RESULTS_PATH = os.path.join(PATH, 'results')
FIG_DIR = os.path.join(PATH, 'figures')

MODEL = 'neural_net'
# preferred display order + labels (datasets not present are skipped)
DATASET_ORDER = ['hopv15_exp', 'freesolv', 'bace', 'lipop', 'aqsoldb', 'clogp',
                 'compas', 'qm9_smiles', 'zinc250']
DATASET_LABEL = {'hopv15_exp': 'HOPV15', 'freesolv': 'FreeSolv', 'bace': 'BACE',
                 'lipop': 'Lipophilicity', 'aqsoldb': 'AqSolDB', 'clogp': 'ClogP',
                 'compas': 'COMPAS-3x', 'qm9_smiles': 'QM9', 'zinc250': 'ZINC250k'}

apply_style()


def load_prediction():
    """(dataset, method) -> list of test R^2 across seeds for the NN regressor."""
    data = defaultdict(list)
    for path, namespace, meta, params in iter_archives(RESULTS_PATH):
        if not namespace.startswith('predict_molecules'):
            continue
        method = method_of(namespace)
        dataset = dataset_of(namespace)
        if method not in ('hdc', 'fp'):
            continue
        dj = os.path.join(path, 'experiment_data.json')
        if not os.path.exists(dj):
            continue
        try:
            metrics = json.load(open(dj)).get('metrics', {})
        except Exception:
            continue
        entry = metrics.get(f'test_{MODEL}')
        if isinstance(entry, dict) and 'r2' in entry:
            data[(dataset, method)].append(float(entry['r2']))
    return data


def main():
    data = load_prediction()
    if not data:
        raise SystemExit(f'No predict_molecules archives found under {RESULTS_PATH}.')

    datasets = [d for d in DATASET_ORDER if (d, 'hdc') in data or (d, 'fp') in data]
    extra = sorted({d for (d, _m) in data} - set(datasets))
    datasets += extra
    print('prediction datasets:', datasets)

    fig, ax = plt.subplots(figsize=(max(7.0, 1.15 * len(datasets) + 2), 4.6))
    x = np.arange(len(datasets))
    bw = 0.38
    specs = [('fp', COLOR_FP, COLOR_FP_FILL, -0.5, 'Morgan FP'),
             ('hdc', COLOR_HDC, COLOR_HDC_FILL, 0.5, 'HDF (ours)')]

    mean_lo = 0.0
    for method, edge, fill, off, _label in specs:
        means, stds = [], []
        for d in datasets:
            vals = data.get((d, method), [])
            means.append(np.mean(vals) if vals else np.nan)
            stds.append(np.std(vals) if len(vals) > 1 else 0.0)
        means = np.array(means)
        stds = np.array(stds)
        mean_lo = min(mean_lo, np.nanmin(means))
        ax.bar(x + off * bw, means, width=bw * 0.92, color=fill, edgecolor=edge,
               linewidth=1.4, yerr=stds, capsize=3,
               error_kw=dict(linewidth=1.2, ecolor='#444444'), zorder=3)

    # Floor the axis at 0 (R^2 convention): noisy lower whiskers on tiny datasets
    # (e.g. HOPV15, 175 molecules) then clip at the axis instead of dominating it.
    if mean_lo < 0:
        ax.axhline(0, color='#666666', linewidth=1.0, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels([DATASET_LABEL.get(d, d) for d in datasets])
    ax.set_ylabel(r'Test $R^2$ (neural network)  $\uparrow$')
    ax.set_ylim(min(0.0, mean_lo - 0.05), 1.0)
    ax.set_title('Molecular property prediction')
    ax.grid(True, axis='y')
    ax.grid(False, axis='x')

    handles = [Patch(facecolor=COLOR_FP_FILL, edgecolor=COLOR_FP, linewidth=1.4,
                     label='Morgan FP'),
               Patch(facecolor=COLOR_HDC_FILL, edgecolor=COLOR_HDC, linewidth=1.4,
                     label='HDF (ours)')]
    ax.legend(handles=handles, loc='lower left')

    fig.tight_layout()
    save_figure(fig, FIG_DIR, 'figure_prediction')


if __name__ == '__main__':
    main()
