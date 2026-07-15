"""Hyperdimensional computing for graph structures (graph_hdc).

Encodes graphs into high-dimensional hypervectors via message passing and
algebraic binding, and decodes them back to recover structural information. See
``graph_hdc.models`` for the ``HyperNet`` encoder family.
"""
import os

_here = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(_here, 'VERSION')) as _f:
        __version__ = _f.read().strip()
except OSError:  # pragma: no cover
    __version__ = '0.1.0'
