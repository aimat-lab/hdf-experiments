"""
Static checks of the protocol command files in code/protocols/: every line calls a script of
code/experiments/fingerprints, and every --PARAM of a pycomex experiment is a parameter of that experiment (a
module-level upper-case name of the script, of the modules it extends or of an included mixin, or a special pycomex
parameter). This catches parameters renamed or removed after a protocol was recorded.
"""
import os
import re
import shlex

import pytest

CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTOCOLS = os.path.join(CODE, 'protocols')
EXPERIMENTS = os.path.join(CODE, 'experiments', 'fingerprints')

SPECIAL = {'__DEBUG__', '__PREFIX__', '__CACHING__', '__INCLUDE__', '__TESTING__', '__REPRODUCIBLE__', '__NAME__'}
PROTOCOL_FILES = sorted(f for f in os.listdir(PROTOCOLS) if f.endswith('.txt')) if os.path.isdir(PROTOCOLS) else []


def module_parameters(script: str, seen=None) -> set:
    """Upper-case module-level names of a pycomex script and of the modules it extends (Experiment.extend)."""
    seen = set() if seen is None else seen
    if script in seen:
        return set()
    seen.add(script)
    with open(os.path.join(EXPERIMENTS, script)) as f:
        source = f.read()
    names = set(re.findall(r'^([A-Z][A-Z0-9_]*)\s*(?::[^=\n]*)?=', source, re.M))
    for parent in re.findall(r"Experiment\.extend\(\s*['\"]([^'\"]+\.py)['\"]", source):
        names |= module_parameters(parent, seen)
    return names


def is_pycomex(script: str) -> bool:
    with open(os.path.join(EXPERIMENTS, script)) as f:
        source = f.read()
    return 'Experiment(' in source or 'Experiment.extend(' in source


def protocol_lines(name: str):
    with open(os.path.join(PROTOCOLS, name)) as f:
        for number, line in enumerate(f, start=1):
            line = line.strip()
            if line and not line.startswith('#'):
                yield number, line


@pytest.mark.parametrize('name', PROTOCOL_FILES)
def test_protocol_lines_call_existing_scripts_with_known_parameters(name):
    cache = {}
    problems = []
    for number, line in protocol_lines(name):
        tokens = shlex.split(line)
        if len(tokens) < 2 or tokens[0] != 'python' or not tokens[1].endswith('.py'):
            problems.append(f'line {number}: not a "python <script>.py ..." command')
            continue
        script = tokens[1]
        if not os.path.isfile(os.path.join(EXPERIMENTS, script)):
            problems.append(f'line {number}: script {script} missing')
            continue
        if not is_pycomex(script):
            continue
        params = [t[2:].split('=', 1)[0] for t in tokens[2:] if t.startswith('--') and '=' in t]
        includes = [t.split('=', 1)[1].strip('\'"') for t in tokens[2:] if t.startswith('--__INCLUDE__=')]
        key = (script, tuple(includes))
        if key not in cache:
            known = module_parameters(script)
            for include in includes:
                known |= module_parameters(include)
            cache[key] = known | SPECIAL
        unknown = sorted(set(params) - cache[key])
        if unknown:
            problems.append(f'line {number}: {script} has no parameter(s) {unknown}')
    assert not problems, '\n'.join(problems[:20])


@pytest.mark.parametrize('name', PROTOCOL_FILES)
def test_protocol_has_header_and_no_absolute_paths(name):
    with open(os.path.join(PROTOCOLS, name)) as f:
        text = f.read()
    assert text.startswith('# '), 'protocol files start with a comment header'
    assert '# Paper:' in text
    for number, line in protocol_lines(name):
        assert not re.search(r'(^|[\s="\'])/(home|media|p|hkfs|tmp|scratch)/', line), f'line {number}: absolute path'
