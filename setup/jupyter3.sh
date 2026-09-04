#!/bin/bash
# Start the Python 3 Jupyter Notebook server for the L50 labs (run on Machine A).
#
# Usage:  bash setup/jupyter3.sh <crsid> [extra jupyter options]
#
# Uses the self-contained Python 3 stack in /opt/miniforge3/envs/l50 (installed
# once per machine by setup/install_py3_jupyter.sh). It does not use, and does
# not change, the system python/python3 or the old Python 2 Jupyter.
set -euo pipefail

CRSID=${1:-}
if [ -z "$CRSID" ]; then
    echo "usage: $0 <crsid> [extra jupyter options]" >&2
    exit 1
fi
shift

JUPYTER=/opt/miniforge3/envs/l50/bin/jupyter
if [ ! -x "$JUPYTER" ]; then
    echo "The Python 3 Jupyter stack is not installed on this machine." >&2
    echo "Ask the course staff, or run: bash setup/install_py3_jupyter.sh $CRSID" >&2
    exit 1
fi

DIR=/root/$CRSID/L50/Jupyter
if [ ! -d "$DIR" ]; then
    echo "$DIR does not exist: clone the repository under /root/$CRSID first." >&2
    exit 1
fi

# --no-browser: you open the printed URL in the browser on your own laptop
# through an ssh port forward (see README.md). If port 8888 is taken by
# another team, Jupyter picks the next free port; use the port it prints.
exec "$JUPYTER" notebook --allow-root --no-browser --ip 127.0.0.1 \
    --notebook-dir="$DIR" "$@"
