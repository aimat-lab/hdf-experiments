# Reproducible environment for the Hyperdimensional Fingerprints (HDF) artifact.
#
# On Code Ocean the base image is usually pulled from the Code Ocean registry;
# this public base (python:3.11-slim, matching the development interpreter
# 3.11.10) builds identically on any Docker host so reviewers can rebuild
# locally. Pinned third-party versions live in ../requirements.txt.
FROM python:3.11-slim

# -- system libraries required by RDKit, matplotlib, cairosvg (pulled in by
#    chem-mat-database) and other scientific wheels --
RUN apt-get update -q && apt-get install -y --no-install-recommends \
        build-essential git \
        libxrender1 libxext6 libsm6 libgl1 \
        libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLBACKEND=Agg

# -- CPU build of PyTorch first (avoids the large CUDA wheels) --
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.9.1

# -- remaining pinned third-party dependencies --
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# -- packages distributed via git (not on PyPI) --
#    chem-mat-database: dataset access by identifier
#    vgd_counterfactuals: n-hop molecular neighborhood generation for the GED
#      correlation experiment (pulls in visual-graph-datasets)
RUN pip install "chem_mat_database @ git+https://github.com/the16thpythonist/chem_mat_data.git" \
    && pip install "vgd_counterfactuals @ git+https://github.com/the16thpythonist/vgd_counterfactuals.git"

# The library `graph_hdc` is NOT pip-installed: it is vendored under /code and
# imported directly (Code Ocean sets the working directory to /code at run time).
