# hash:sha256:ce0d4871776245aa971b24a9b1b466be6b7edc4c5f50772b0f2741d2d000eb35
FROM registry.codeocean.com/codeocean/py-r:python3.12.8-R4.4.2-JupyterLab4.3.5-RStudiorstudio-server-2024.12.1-563-ubuntu22.04

# Reproducible environment for the Hyperdimensional Fingerprints (HDF) artifact.
#
# The base image above is a Code Ocean starter environment (Code Ocean only
# accepts base images from its own `registry.codeocean.com` registry; public
# Docker Hub images such as python:3.11-slim are rejected). NOTE: this base ships
# Python 3.12.8, whereas the paper's results were generated on Python 3.11.10;
# every version pinned in ../requirements.txt provides 3.12 wheels, so the stack
# installs and runs cleanly. The leading `# hash:` line is Code Ocean's digest
# pin for the base image -- keep it.
#
# Switch to root so the apt-get step below can install system packages (Code
# Ocean base images default to a non-root user).
USER 0:0

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
#    These are inlined (rather than `COPY requirements.txt` + `pip install -r`)
#    because Code Ocean's environment build context is the `environment/` folder
#    and cannot access the repo-root requirements.txt. This list must mirror
#    ../requirements.txt exactly.
RUN pip install \
        torch-geometric==2.6.1 \
        pytorch-lightning==2.5.2 \
        pycomex==0.28.0 \
        rdkit==2025.9.1 \
        scikit-learn==1.6.1 \
        numpy==1.26.4 \
        scipy==1.16.3 \
        pandas==2.2.1 \
        botorch==0.16.0 \
        gpytorch==1.14.2 \
        matplotlib==3.10.7 \
        seaborn==0.13.2 \
        umap-learn==0.5.7 \
        imbalanced-learn==0.13.0 \
        normflows==1.7.3 \
        networkx==3.3 \
        jsonpickle==4.1.1 \
        python-decouple==3.8 \
        rich-click==1.8.9 \
        click==8.3.0 \
        jinja2==3.1.6

# -- packages distributed via git (not on PyPI) --
#    chem-mat-database: dataset access by identifier
#    vgd_counterfactuals: n-hop molecular neighborhood generation for the GED
#      correlation experiment (pulls in visual-graph-datasets)
RUN pip install "chem_mat_database @ git+https://github.com/the16thpythonist/chem_mat_data.git" \
    && pip install "vgd_counterfactuals @ git+https://github.com/the16thpythonist/vgd_counterfactuals.git"

# The library `graph_hdc` is NOT pip-installed: it is vendored under /code and
# imported directly (Code Ocean sets the working directory to /code at run time).
