"""
Run (parts of) the full protocol of one paper experiment from its command file in ``protocols/``.

Every file ``protocols/<experiment>.txt`` lists the exact command lines behind one or more items of the revised paper
(see its header and the README). The lines run from ``experiments/fingerprints``. ``# @stage <name>`` lines split a
file into stages that run one after the other (warmup and primer runs, which write shared caches, before the runs
that read them); the lines of a stage are independent and run in parallel (``--jobs``).

Most protocols took tens to thousands of CPU or GPU hours on HPC clusters, so this script also selects parts of them:

    python run_protocol.py ex_27 --list                         # header, stages and number of lines
    python run_protocol.py ex_27 --stage warmup_fixed --stage fixed --grep "'bace_reg'" --grep "SEED=\\"0\\"" --jobs 2
    python run_protocol.py ex_20 --limit 7 --dry-run             # print the first 7 lines of every stage
    python run_protocol.py ex_14 --grep freesolv --set EPOCHS=5  # override a parameter (smoke test)

Without a GPU (or with ``--cpu``), the device parameters of the paper's GPU runs ('cuda') are replaced by 'cpu'; the
results are the same up to floating-point differences (graph_hdc's ex_27 checked this for the MLP and the KNN). Every
line gets its own log file and temporary folder (TMPDIR) in ``--log-dir``; the script exits with status 1 if any line
failed. Load a dataset once (e.g. by running one line) before running many lines on it in parallel: concurrent first
downloads into the chem_mat_data cache can corrupt it.
"""
import argparse
import os
import re
import shlex
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

CODE = os.path.dirname(os.path.abspath(__file__))
PROTOCOLS = os.path.join(CODE, 'protocols')
EXPERIMENTS = os.path.join(CODE, 'experiments', 'fingerprints')


def read_protocol(name: str):
    """(header lines, [(stage, [command lines])]) of protocols/<name>.txt."""
    path = name if os.path.isfile(name) else os.path.join(PROTOCOLS, f'{name}.txt')
    if not os.path.isfile(path):
        available = sorted(f[:-4] for f in os.listdir(PROTOCOLS) if f.endswith('.txt'))
        raise SystemExit(f'no protocol "{name}"; available: {", ".join(available)}')
    header, stages = [], []
    with open(path) as f:
        for raw in f:
            line = raw.rstrip('\n')
            if line.startswith('# @stage'):
                stages.append((line.split(None, 2)[2].strip(), []))
            elif line.startswith('#') or not line.strip():
                if not stages:
                    header.append(line)
            else:
                if not stages:
                    stages.append(('main', []))
                stages[-1][1].append(line.strip())
    return header, stages


def cuda_available() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


def apply_overrides(line: str, overrides: dict, cpu: bool) -> str:
    """Replace (or append) --KEY="value" arguments; map 'cuda' devices to 'cpu' if requested."""
    tokens = shlex.split(line)
    out = []
    seen = set()
    for token in tokens:
        match = re.match(r'^--([A-Za-z_][A-Za-z0-9_]*)=(.*)$', token, re.S)
        if match:
            key, value = match.groups()
            if key in overrides:
                value = overrides[key]
                seen.add(key)
            if cpu and value in ("'cuda'", '"cuda"', 'cuda'):
                value = "'cpu'"
            out.append(f'--{key}={double_quoted(value)}')
            continue
        elif cpu and token == 'cuda':
            token = 'cpu'
        out.append(shlex.quote(token))
    # parameters the line does not set are appended if the script (or a module it extends) defines them
    script = tokens[1] if len(tokens) > 1 else ''
    for key, value in overrides.items():
        if key not in seen and (key.startswith('__') or key in module_parameters(script)):
            out.append(f'--{key}={double_quoted(value)}')
    return ' '.join(out)


def module_parameters(script: str, seen=None) -> set:
    """Upper-case module-level names of an experiment script and of the modules it extends (Experiment.extend)."""
    seen = set() if seen is None else seen
    path = os.path.join(EXPERIMENTS, script)
    if script in seen or not os.path.isfile(path):
        return set()
    seen.add(script)
    with open(path) as f:
        source = f.read()
    names = set(re.findall(r'^([A-Z][A-Z0-9_]*)\s*(?::[^=\n]*)?=', source, re.M))
    for parent in re.findall(r"Experiment\.extend\(\s*['\"]([^'\"]+\.py)['\"]", source):
        names |= module_parameters(parent, seen)
    return names


def double_quoted(value: str) -> str:
    """A shell word in the style of the protocol files: --KEY="value"."""
    for char in ('\\', '"', '$', '`'):
        value = value.replace(char, '\\' + char)
    return f'"{value}"'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('protocol', help='name of a file in protocols/ (e.g. ex_27) or a path')
    parser.add_argument('--list', action='store_true', help='show the header and the stages, run nothing')
    parser.add_argument('--stage', action='append', default=[], help='run only this stage (repeatable)')
    parser.add_argument('--grep', action='append', default=[],
                        help='run only lines that contain this regular expression (repeatable: all must match)')
    parser.add_argument('--limit', type=int, default=None, help='at most this many lines per stage')
    parser.add_argument('--set', action='append', default=[], metavar='KEY=VALUE',
                        help='override a parameter of the selected lines (VALUE as a Python literal, e.g. '
                             "EPOCHS=5 or DATASET_NAME=\"'freesolv'\"); added to lines that do not set it only if "
                             'their script defines the parameter')
    parser.add_argument('--jobs', type=int, default=1, help='lines of a stage that run in parallel (default 1)')
    parser.add_argument('--threads', type=int, default=2, help='OMP/MKL threads per line (default 2)')
    parser.add_argument('--cpu', action='store_true', help="replace 'cuda' by 'cpu' even if a GPU is available")
    parser.add_argument('--dry-run', action='store_true', help='print the selected lines, run nothing')
    parser.add_argument('--keep-going', action='store_true',
                        help='start the next stage even if a line of the previous one failed (by default the run '
                             'stops: a failed warmup can leave a truncated cache file behind)')
    parser.add_argument('--log-dir', default=os.path.join(EXPERIMENTS, 'logs'), help='one log file per line')
    args = parser.parse_args()

    header, stages = read_protocol(args.protocol)
    if args.list:
        print('\n'.join(header))
        for stage, lines in stages:
            print(f'  stage {stage}: {len(lines)} lines')
        return

    overrides = {}
    for item in args.set:
        key, _, value = item.partition('=')
        overrides[key.strip()] = value
    cpu = args.cpu or not cuda_available()

    env = dict(os.environ)
    env['PYTHONPATH'] = CODE + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    env.setdefault('MPLBACKEND', 'Agg')
    for var in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
        env[var] = str(args.threads)
    if cpu:
        env['CUDA_VISIBLE_DEVICES'] = ''

    selected = []
    for stage, lines in stages:
        if args.stage and stage not in args.stage:
            continue
        lines = [line for line in lines if all(re.search(pattern, line) for pattern in args.grep)]
        if args.limit is not None:
            lines = lines[:args.limit]
        if lines:
            selected.append((stage, [apply_overrides(line, overrides, cpu) for line in lines]))
    if not selected:
        raise SystemExit('no lines selected')

    if args.dry_run:
        for stage, lines in selected:
            print(f'# @stage {stage}  ({len(lines)} lines)')
            print('\n'.join(lines))
        return

    name = os.path.splitext(os.path.basename(args.protocol))[0]
    log_dir = os.path.join(args.log_dir, name)
    os.makedirs(log_dir, exist_ok=True)
    failed = []

    def run(item):
        index, stage, line = item
        log = os.path.join(log_dir, f'{stage}__{index:05d}.log')
        start = time.time()
        with open(log, 'w') as f:
            f.write(line + '\n\n')
            f.flush()
            # a private temporary folder per line, as in the paper's runs: chem_mat_data and predict_bioactivity write
            # into the temporary folder, and parallel runs on the same dataset must not share it
            tmp = os.path.join(log_dir, 'tmp', f'{stage}__{index:05d}')
            os.makedirs(tmp, exist_ok=True)
            code = subprocess.call(['bash', '-c', line], cwd=EXPERIMENTS, env={**env, 'TMPDIR': tmp},
                                   stdout=f, stderr=subprocess.STDOUT)
        status = 'ok' if code == 0 else f'FAILED (exit {code})'
        print(f'[{stage} {index}] {status} after {time.time() - start:.0f} s  (log: {log})', flush=True)
        return code, log

    for stage, lines in selected:
        print(f'=== stage {stage}: {len(lines)} lines, {args.jobs} in parallel', flush=True)
        items = [(i, stage, line) for i, line in enumerate(lines)]
        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            for code, log in pool.map(run, items):
                if code != 0:
                    failed.append(log)
        if failed and not args.keep_going:
            print(f'stopping after stage {stage}: {len(failed)} line(s) failed')
            break
    if failed:
        print(f'{len(failed)} line(s) failed:\n  ' + '\n  '.join(failed))
        sys.exit(1)
    print('all lines finished')


if __name__ == '__main__':
    main()
