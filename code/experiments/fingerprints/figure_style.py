"""
Shared plotting style and archive helpers for the paper-quality artifact figures.

All three figure scripts (``make_figure_ged``, ``make_figure_bo``,
``make_figure_prediction``) import from here so that colours, typography and
archive discovery stay consistent and match the style of the paper.
"""
import os
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# -- paper palette (HDF green, Morgan blue, random grey) ----------------------
COLOR_HDC = '#2FB877'        # hyperdimensional fingerprints (line)
COLOR_HDC_FILL = '#4CEB99'   # ... and the lighter box/band fill
COLOR_FP = '#4C64EB'         # Morgan fingerprints (line)
COLOR_FP_FILL = '#9AABF5'    # ... and the lighter box/band fill
COLOR_RANDOM = '#8A9099'     # random representation baseline

METHOD_COLOR = {'hdc': COLOR_HDC, 'fp': COLOR_FP, 'random': COLOR_RANDOM}
METHOD_FILL = {'hdc': COLOR_HDC_FILL, 'fp': COLOR_FP_FILL, 'random': '#C7CBD1'}
METHOD_LABEL = {'hdc': 'HDF (ours)', 'fp': 'Morgan FP', 'random': 'Random'}


def apply_style():
    """Apply the shared rcParams. Call once at the top of each figure script."""
    plt.rcParams.update({
        'font.family': 'DejaVu Sans',
        'font.size': 11,
        'axes.titlesize': 13,
        'axes.titleweight': 'bold',
        'axes.labelsize': 12,
        'axes.edgecolor': '#333333',
        'axes.linewidth': 1.0,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'axes.axisbelow': True,
        'grid.color': '#B4B4B4',
        'grid.alpha': 0.35,
        'grid.linewidth': 0.7,
        'xtick.color': '#333333',
        'ytick.color': '#333333',
        'xtick.labelsize': 10.5,
        'ytick.labelsize': 10.5,
        'legend.frameon': True,
        'legend.framealpha': 0.92,
        'legend.edgecolor': '#CCCCCC',
        'legend.fontsize': 10.5,
        'figure.facecolor': 'white',
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'svg.fonttype': 'none',
    })


# -- archive discovery --------------------------------------------------------
# pycomex stores the concrete parameter values in ``experiment_meta.json`` (not
# ``experiment_data.json``), so we read them from there. Archives are detected
# by the presence of that file; the top-level directory under results/ is the
# experiment "namespace" (e.g. ``predict_molecules__hdc__bace``).

def iter_archives(results_path):
    """Yield ``(archive_path, namespace, meta, params)`` for every archive."""
    if not os.path.isdir(results_path):
        return
    for dirpath, dirnames, filenames in os.walk(results_path):
        if 'experiment_meta.json' not in filenames:
            continue
        dirnames.clear()  # an archive never contains nested archives
        try:
            meta = json.loads(open(os.path.join(dirpath, 'experiment_meta.json')).read())
        except Exception:
            continue
        params = {
            p: info['value']
            for p, info in meta.get('parameters', {}).items()
            if isinstance(info, dict) and 'value' in info
        }
        namespace = os.path.relpath(dirpath, results_path).split(os.sep)[0]
        yield dirpath, namespace, meta, params


def method_of(namespace):
    """'predict_molecules__hdc__bace' -> 'hdc' (also 'fp'/'random')."""
    for tok in ('random', 'hdc', 'fp'):
        if f'__{tok}__' in namespace or namespace.endswith(f'__{tok}'):
            return tok
    return 'unknown'


def dataset_of(namespace):
    """Last token of the namespace, e.g. '...__hdc__bace' -> 'bace'."""
    parts = namespace.split('__')
    return parts[-1] if len(parts) > 2 else ''


def save_figure(fig, out_dir, stem):
    """Save a figure as PDF (vector, paper), SVG (editable) and PNG (preview)."""
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for ext in ('pdf', 'svg', 'png'):
        p = os.path.join(out_dir, f'{stem}.{ext}')
        fig.savefig(p)
        paths.append(p)
    print(f'saved {stem}.pdf / .svg / .png -> {out_dir}')
    return paths
