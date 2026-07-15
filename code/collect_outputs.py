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
from collections import defaultdict


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
        # pycomex does not persist a `parameters` block, so derive the
        # experiment family / representation / dataset from the namespace,
        # e.g. "predict_molecules__hdc__bace" -> (predict_molecules, hdc, bace).
        parts = namespace.split('__')
        family = parts[0]
        method = parts[1] if len(parts) > 2 else ''
        dataset = parts[-1] if len(parts) > 2 else (parts[1] if len(parts) > 1 else '')
        run_id = os.path.basename(rel)  # distinguishes seeds/repetitions
        row = {
            'family': family,
            'method': method,
            'dataset': dataset,
            'run': run_id,
            'metrics': flatten_metrics(data.get('metrics', {})),
        }
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

    # --- write summary.csv: one row per archive, its own metrics inline ---
    csv_path = os.path.join(results_dir, 'summary.csv')
    metric_keys = []
    for r in rows:
        for k in r['metrics']:
            if k not in metric_keys:
                metric_keys.append(k)
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['family', 'method', 'dataset', 'run'] + metric_keys)
        for r in rows:
            w.writerow([r['family'], r['method'], r['dataset'], r['run']]
                       + [r['metrics'].get(k, '') for k in metric_keys])

    # --- write summary.md: grouped by family, each row shows its own metrics ---
    def fmt(v):
        return f'{v:.4g}' if isinstance(v, float) else str(v)

    md_path = os.path.join(results_dir, 'summary.md')
    with open(md_path, 'w') as f:
        f.write('# Reproducible-run summary\n\n')
        f.write(f'- experiment archives found: **{len(rows)}**\n')
        f.write(f'- figures collected: **{n_figs}** (see `figures/`)\n\n')
        by_family = defaultdict(list)
        for r in rows:
            by_family[r['family']].append(r)
        for family in sorted(by_family):
            frows = by_family[family]
            # columns = the metric keys actually present in this family
            fkeys = []
            for r in frows:
                for k in r['metrics']:
                    if k not in fkeys:
                        fkeys.append(k)
            fkeys = fkeys[:12]
            f.write(f'## {family}\n\n')
            head = ['method', 'dataset', 'run'] + fkeys
            f.write('| ' + ' | '.join(head) + ' |\n')
            f.write('| ' + ' | '.join('---' for _ in head) + ' |\n')
            for r in sorted(frows, key=lambda x: (x['method'], x['dataset'], x['run'])):
                cells = [r['method'], r['dataset'], r['run']] + \
                        [fmt(r['metrics'].get(k, '')) for k in fkeys]
                f.write('| ' + ' | '.join(cells) + ' |\n')
            f.write('\n')

    print(f'\nWrote {csv_path}')
    print(f'Wrote {md_path}')
    print(f'Collected {n_figs} figure(s) into {fig_out}')
    print(f'Summarized {len(rows)} experiment archive(s)')


if __name__ == '__main__':
    main()
