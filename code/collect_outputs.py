"""
Collect the outputs of a reproducible run into a single, browsable results
directory: a metrics summary table plus every figure that any experiment (or the
figure scripts) produced.

This walks the pycomex experiment archives under ``<experiments_dir>/results``,
reads the ``experiment_data.json`` metrics from each, writes ``summary.csv`` and
``summary.md``, and copies every ``*.pdf``/``*.png``/``*.svg`` it finds into
``<results_dir>/figures`` with a namespaced filename so nothing collides.

Usage::

    python collect_outputs.py experiments/fingerprints /results
"""
import os
import sys
import csv
import json
import shutil


def find_archives(results_root: str):
    """Yield every directory that looks like a pycomex experiment archive."""
    for dirpath, _dirnames, filenames in os.walk(results_root):
        if 'experiment_data.json' in filenames or 'experiment_meta.json' in filenames:
            yield dirpath


def flatten_metrics(metrics: dict, prefix: str = '') -> dict:
    """Recursively flatten a (possibly deeply nested) metrics dict to dotted
    keys with numeric leaves, e.g. ``neural_net.test.mae -> 0.84``. Handles both
    the per-model regression metrics (predict_molecules) and the flat scalar
    metrics (optimize_molecule_bo)."""
    out = {}
    for key, val in (metrics or {}).items():
        name = f'{prefix}.{key}' if prefix else str(key)
        if isinstance(val, dict):
            out.update(flatten_metrics(val, name))
        elif isinstance(val, bool):
            continue
        elif isinstance(val, (int, float)):
            out[name] = val
    return out


def main() -> None:
    exp_dir = sys.argv[1] if len(sys.argv) > 1 else 'experiments/fingerprints'
    results_dir = sys.argv[2] if len(sys.argv) > 2 else '/results'
    results_root = os.path.join(exp_dir, 'results')
    fig_out = os.path.join(results_dir, 'figures')
    os.makedirs(fig_out, exist_ok=True)

    rows = []
    n_figs = 0
    for archive in sorted(find_archives(results_root)):
        rel = os.path.relpath(archive, results_root)
        namespace = rel.split(os.sep)[0]

        # --- metrics ---
        data = {}
        dj = os.path.join(archive, 'experiment_data.json')
        if os.path.exists(dj):
            try:
                data = json.load(open(dj))
            except Exception as exc:
                print(f'  ! could not read {dj}: {exc}')
        params = data.get('parameters', {}) or {}
        row = {
            'namespace': namespace,
            'archive': rel,
            'dataset': params.get('DATASET_NAME'),
            'prefix': params.get('__PREFIX__'),
        }
        row.update(flatten_metrics(data.get('metrics', {})))
        rows.append(row)

        # --- figures produced inside the archive ---
        for fn in os.listdir(archive):
            if fn.lower().endswith(('.pdf', '.png', '.svg')):
                dst = os.path.join(fig_out, f'{namespace}__{fn}')
                try:
                    shutil.copy2(os.path.join(archive, fn), dst)
                    n_figs += 1
                except Exception as exc:
                    print(f'  ! could not copy {fn}: {exc}')

    # --- figures produced by the standalone figure scripts (e.g. figure_ged) ---
    script_fig_dir = os.path.join(exp_dir, 'figures')
    if os.path.isdir(script_fig_dir):
        for fn in os.listdir(script_fig_dir):
            if fn.lower().endswith(('.pdf', '.png', '.svg')):
                try:
                    shutil.copy2(os.path.join(script_fig_dir, fn),
                                 os.path.join(fig_out, fn))
                    n_figs += 1
                except Exception as exc:
                    print(f'  ! could not copy {fn}: {exc}')

    # --- write the summary table ---
    all_cols = []
    for r in rows:
        for k in r:
            if k not in all_cols:
                all_cols.append(k)

    csv_path = os.path.join(results_dir, 'summary.csv')
    with open(csv_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=all_cols)
        w.writeheader()
        w.writerows(rows)

    md_path = os.path.join(results_dir, 'summary.md')
    with open(md_path, 'w') as f:
        f.write(f'# Reproducible-run summary\n\n')
        f.write(f'- experiment archives found: **{len(rows)}**\n')
        f.write(f'- figures collected: **{n_figs}** (see `figures/`)\n\n')
        # compact per-archive metric view
        metric_cols = [c for c in all_cols
                       if c not in ('namespace', 'archive', 'dataset', 'prefix')]
        show = ['namespace', 'dataset'] + metric_cols[:8]
        f.write('| ' + ' | '.join(show) + ' |\n')
        f.write('| ' + ' | '.join('---' for _ in show) + ' |\n')
        for r in rows:
            f.write('| ' + ' | '.join(
                f'{r.get(c, "")}' if not isinstance(r.get(c), float)
                else f'{r.get(c):.4g}' for c in show) + ' |\n')

    print(f'\nWrote {csv_path}')
    print(f'Wrote {md_path}')
    print(f'Collected {n_figs} figure(s) into {fig_out}')
    print(f'Summarized {len(rows)} experiment archive(s)')


if __name__ == '__main__':
    main()
