"""
figure_prediction -- Property prediction accuracy.

Grouped bars of the test-set coefficient of determination (R^2, higher is
better) of the MLP of Table 1 (left) and the KNN of Supplementary Table S6
(right), trained on Morgan fingerprints vs hyperdimensional fingerprints (HDF),
across molecular property datasets. Bars show the mean over the seeds (splits);
error bars are +/- one standard deviation.

Data: ``predict_molecules__{fp,hdc}__*`` archives of the reproducible run
(prefix ``demo_tables``), reading ``metrics.test_<model>.r2`` from
``experiment_data.json``.

Usage::

    python demo_figure_prediction.py
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

PREFIX = os.environ.get('DEMO_PREFIX_TABLES', 'demo_tables')
# (model, panel title): the MLP of Table 1 and the KNN of Supplementary Table S6
MODELS = [('neural_net2', 'MLP (Table 1 protocol)'), ('k_neighbors', 'KNN, k = 5 (Table S6 protocol)')]
# preferred display order + labels (datasets not present are skipped)
DATASET_ORDER = ['hopv15_exp', 'freesolv', 'bace', 'lipop', 'aqsoldb', 'clogp',
                 'compas', 'qm9_smiles', 'zinc250']
DATASET_LABEL = {'hopv15_exp': 'HOPV15', 'freesolv': 'FreeSolv', 'bace': 'BACE',
                 'lipop': 'Lipophilicity', 'aqsoldb': 'AqSolDB', 'clogp': 'ClogP',
                 'compas': 'COMPAS-3x', 'qm9_smiles': 'QM9', 'zinc250': 'ZINC250k'}

apply_style()


def load_prediction(model):
    """(dataset, method) -> list of test R^2 across seeds for one downstream model."""
    data = defaultdict(list)
    for path, namespace, meta, params in iter_archives(RESULTS_PATH):
        if not namespace.startswith('predict_molecules'):
            continue
        if str(params.get('__PREFIX__', '')) != PREFIX:
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
        entry = metrics.get(f'test_{model}')
        if isinstance(entry, dict) and 'r2' in entry:
            data[(dataset, method)].append(float(entry['r2']))
    return data


def main():
    panels = [(model, title, load_prediction(model)) for model, title in MODELS]
    panels = [p for p in panels if p[2]]
    if not panels:
        raise SystemExit(f'No predict_molecules archives with prefix {PREFIX} found under {RESULTS_PATH}.')

    present = {d for _m, _t, data in panels for (d, _method) in data}
    datasets = [d for d in DATASET_ORDER if d in present] + sorted(present - set(DATASET_ORDER))
    print('prediction datasets:', datasets)

    width = max(7.0, 1.15 * len(datasets) + 2)
    fig, axes = plt.subplots(1, len(panels), figsize=(width * len(panels), 4.6), squeeze=False)
    x = np.arange(len(datasets))
    bw = 0.38
    specs = [('fp', COLOR_FP, COLOR_FP_FILL, -0.5, 'Morgan FP'),
             ('hdc', COLOR_HDC, COLOR_HDC_FILL, 0.5, 'HDF (ours)')]

    for ax, (model, title, data) in zip(axes[0], panels):
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

        # Floor the axis at 0 (R^2 convention): noisy lower whiskers on small datasets
        # then clip at the axis instead of dominating it.
        if mean_lo < 0:
            ax.axhline(0, color='#666666', linewidth=1.0, zorder=2)
        ax.set_xticks(x)
        ax.set_xticklabels([DATASET_LABEL.get(d, d) for d in datasets])
        ax.set_ylabel(r'Test $R^2$  $\uparrow$')
        ax.set_ylim(min(0.0, mean_lo - 0.05), 1.0)
        ax.set_title(title)
        ax.grid(True, axis='y')
        ax.grid(False, axis='x')

    handles = [Patch(facecolor=COLOR_FP_FILL, edgecolor=COLOR_FP, linewidth=1.4,
                     label='Morgan FP'),
               Patch(facecolor=COLOR_HDC_FILL, edgecolor=COLOR_HDC, linewidth=1.4,
                     label='HDF (ours)')]
    axes[0][0].legend(handles=handles, loc='lower left')

    fig.tight_layout()
    save_figure(fig, FIG_DIR, 'figure_prediction')


if __name__ == '__main__':
    main()
