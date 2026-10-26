"""
figure_ged -- Correlation with graph edit distance.

For each embedding size, box plots of the |Pearson correlation| between
representation-space distance and graph edit distance (GED), comparing Morgan
fingerprints (radius 2) against hyperdimensional fingerprints (HDF, depth 2).
Higher is better: a faithful representation places structurally similar
molecules close together.

Data: ``molecule_similarity__{fp,hdc}`` archives run with ``__PREFIX__=ex_08_a``,
reading the per-query ``ged_correlation_summary.csv`` (reused, not re-run).

Usage::

    python make_figure_ged.py
"""
import os
import pathlib
from collections import defaultdict

import numpy as np
import pandas as pd
from matplotlib.patches import Patch
import matplotlib.pyplot as plt

from figure_style import (apply_style, iter_archives, method_of,
                          COLOR_FP, COLOR_HDC, COLOR_FP_FILL, COLOR_HDC_FILL,
                          save_figure)

PATH = str(pathlib.Path(__file__).parent.absolute())
RESULTS_PATH = os.path.join(PATH, 'results')
FIG_DIR = os.path.join(PATH, 'figures')
GED_PREFIX = 'ex_08_a'
# Embedding sizes shown, in the paper's canonical set. (Other sizes present in
# the archives are ignored so the demo and paper figures line up.)
GED_SIZES = [32, 128, 512, 2048]

apply_style()


def load_ged():
    """(encoding, size) -> list of |correlation| values across query molecules."""
    data = defaultdict(list)
    for path, namespace, meta, params in iter_archives(RESULTS_PATH):
        if 'molecule_similarity' not in namespace:
            continue
        if str(params.get('__PREFIX__', '')) != GED_PREFIX:
            continue
        enc = method_of(namespace)
        if enc == 'fp':
            size = params.get('FINGERPRINT_SIZE', 0)
        elif enc == 'hdc':
            size = params.get('EMBEDDING_SIZE', 0)
        else:
            continue
        csv_path = os.path.join(path, 'ged_correlation_summary.csv')
        if not os.path.exists(csv_path):
            continue
        df = pd.read_csv(csv_path)
        df = df[df['query_id'].astype(str) != 'AGGREGATE']
        if 'correlation' in df.columns:
            data[(enc, int(size))].extend(df['correlation'].astype(float).abs().tolist())
    return data


def main():
    ged = load_ged()
    if not ged:
        raise SystemExit(f'No GED archives found under {RESULTS_PATH} '
                         f'(need molecule_similarity runs with __PREFIX__={GED_PREFIX}).')

    present = {size for _enc, size in ged}
    sizes = [s for s in GED_SIZES if s in present] or sorted(present)
    print('GED embedding sizes:', sizes,
          '| queries per (enc,size):', {k: len(v) for k, v in sorted(ged.items())})

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    box_w = 0.36
    specs = [('fp', COLOR_FP, COLOR_FP_FILL), ('hdc', COLOR_HDC, COLOR_HDC_FILL)]

    for size_idx, size in enumerate(sizes):
        for enc_idx, (enc, edge, fill) in enumerate(specs):
            vals = ged.get((enc, size), [])
            if not vals:
                continue
            pos = size_idx + (enc_idx - 0.5) * box_w
            ax.boxplot(
                [vals], positions=[pos], widths=box_w * 0.86, patch_artist=True,
                showfliers=True,
                boxprops=dict(facecolor=fill, edgecolor=edge, linewidth=1.4),
                medianprops=dict(color=edge, linewidth=1.8),
                whiskerprops=dict(color=edge, linewidth=1.3),
                capprops=dict(color=edge, linewidth=1.3),
                flierprops=dict(marker='o', markerfacecolor=edge, markeredgecolor='none',
                                markersize=2.5, alpha=0.35),
            )

    ax.set_xticks(range(len(sizes)))
    ax.set_xticklabels(sizes)
    ax.set_xlabel('Embedding size')
    ax.set_ylabel(r'$|\mathrm{Pearson\ correlation\ with\ GED}|\ \uparrow$')
    ax.set_ylim(0, 1.02)
    ax.set_xlim(-0.6, len(sizes) - 0.4)
    ax.set_title('Correlation with graph edit distance')
    ax.grid(True, axis='y')
    ax.grid(False, axis='x')

    handles = [Patch(facecolor=COLOR_FP_FILL, edgecolor=COLOR_FP, linewidth=1.4,
                     label='Morgan FP (radius 2)'),
               Patch(facecolor=COLOR_HDC_FILL, edgecolor=COLOR_HDC, linewidth=1.4,
                     label='HDF (depth 2, ours)')]
    ax.legend(handles=handles, loc='lower right')

    fig.tight_layout()
    save_figure(fig, FIG_DIR, 'figure_ged')


if __name__ == '__main__':
    main()
