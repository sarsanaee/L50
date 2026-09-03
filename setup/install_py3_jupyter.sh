#!/bin/bash
# Install an isolated, current Python 3 + Jupyter Notebook stack for the L50
# labs on the (Ubuntu 16.04) lab machine, WITHOUT touching:
#   - the system python2.7 / python3.5 and the existing Jupyter 5.7 install
#   - DAG, OSNT/NetFPGA drivers and tools, the kernel, or any OS package
#
# Why Miniforge: Ubuntu 16.04 ships OpenSSL 1.0.2 and glibc 2.23, so a source
# build of a modern CPython cannot get a working ssl module (pip would be
# unusable). conda-forge ships its own OpenSSL and needs only glibc >= 2.17.
#
# Usage:  bash setup/install_py3_jupyter.sh [<crsid>]
set -euo pipefail

PREFIX=/opt/miniforge3
ENV=l50
PYVER=3.12
URL=https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
CRSID=${1:-}

if [ ! -x "$PREFIX/bin/conda" ]; then
    echo "==> downloading Miniforge"
    curl -fL -o /tmp/miniforge.sh "$URL"
    bash /tmp/miniforge.sh -b -p "$PREFIX"
fi

if [ ! -x "$PREFIX/envs/$ENV/bin/python" ]; then
    echo "==> creating conda env '$ENV'"
    "$PREFIX/bin/conda" create -y -n "$ENV" "python=$PYVER" notebook ipykernel numpy matplotlib paramiko
fi

echo "==> registering kernel 'python3' -> Python 3 (L50)"
"$PREFIX/envs/$ENV/bin/python" -m ipykernel install --name python3 --display-name "Python 3 (L50)"

# The legacy Python 2 kernelspec (/usr/local/share/jupyter/kernels/python2)
# is left in place, so the new Notebook server offers both kernels.
"$PREFIX/envs/$ENV/bin/jupyter" kernelspec list

cat <<EOF

Done. Start the new notebook server with:

  $PREFIX/envs/$ENV/bin/jupyter notebook --allow-root --no-browser \\
      --notebook-dir=/root/${CRSID:-<crsid>}/L50/Jupyter

The old Python 2 server is untouched: /usr/local/bin/jupyter notebook ...
EOF
