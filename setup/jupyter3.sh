#!/bin/bash
# jupyter3.sh: start, inspect or stop YOUR Python 3 Jupyter Notebook server
# for the L50 labs. Run it on Machine A.
#
#   bash setup/jupyter3.sh <crsid>          start it, or show it if already running
#   bash setup/jupyter3.sh <crsid> status   is it running? print its URL
#   bash setup/jupyter3.sh <crsid> stop     stop it (only yours)
#
# It is safe to run this as often as you like: if your server is already
# running it just prints the URL again and starts nothing. One server per
# crsid; it only ever looks at the server for /root/<crsid>/L50/Jupyter and
# never touches other teams' servers, the system python, or anything else.
#
# The server uses the self-contained Python 3 stack in /opt/miniforge3/envs/l50
# (installed once per machine by staff with setup/install_py3_jupyter.sh).
set -euo pipefail
umask 022

ENV_DIR=/opt/miniforge3/envs/l50
JUPYTER=$ENV_DIR/bin/jupyter
PY=$ENV_DIR/bin/python
WAIT_SECS=30

usage() {
    echo "usage: bash setup/jupyter3.sh <crsid> [start|status|stop]" >&2
    exit 2
}
die() { echo "jupyter3.sh: $*" >&2; exit 1; }

# ---- arguments: exactly <crsid> and an optional action, nothing else --------
[ $# -ge 1 ] && [ $# -le 2 ] || usage
CRSID=$1
ACTION=${2:-start}
[[ $CRSID =~ ^[a-z][a-z0-9]{1,15}$ ]] || die "'$CRSID' does not look like a crsid (lowercase letters and digits)"
case $ACTION in
    start|status|stop) ;;
    *) die "unknown action '$ACTION' (use start, status or stop)" ;;
esac

# ---- environment checks (nothing is changed if any of these fail) ----------
[ "$(id -u)" -eq 0 ] || die "run this as root on Machine A"
[ -x "$JUPYTER" ] && [ -x "$PY" ] || die "the Python 3 Jupyter stack is not installed on this machine ($ENV_DIR). Tell the course staff."
HOME_DIR=/root/$CRSID
NB_DIR=$HOME_DIR/L50/Jupyter
[ -d "$NB_DIR" ] || die "$NB_DIR does not exist. Clone the repository first: see README.md (step 1)."
NB_DIR=$(cd "$NB_DIR" && pwd -P)
LOG=$HOME_DIR/jupyter3.log
LOCK=$HOME_DIR/.jupyter3.lock
HOST=$(hostname -f 2>/dev/null || hostname)
case $HOST in *.*) ;; *) HOST=$HOST.nf.cl.cam.ac.uk ;; esac   # full name for the ssh hint

# ---- find_server: print "<port> <url-with-token>" for a live server whose
#      notebook directory is NB_DIR; print nothing if there is none. ---------
find_server() {
    "$JUPYTER" server list --jsonlist 2>/dev/null | "$PY" -c '
import json, os, sys
want = os.path.realpath(sys.argv[1])
try:
    servers = json.load(sys.stdin)
except Exception:
    servers = []
for s in servers:
    pid = s.get("pid")
    if not pid or not os.path.exists("/proc/%d" % pid):
        continue                      # stale entry from a crashed server
    if os.path.realpath(s.get("root_dir", "")) != want:
        continue                      # a server of another team
    url = s["url"].rstrip("/") + "/tree?token=" + s.get("token", "")
    print("%s %s" % (s["port"], url))
    break
' "$NB_DIR" || true
}

# ---- server_pids: independent second check straight from the process list:
#      pids of notebook servers started for NB_DIR (crsid is [a-z0-9] so the
#      path is regex-safe). Used so that we never start a second server even
#      if the registry above is empty or broken. --------------------------
server_pids() {
    pgrep -f -- "jupyter-notebook .*--notebook-dir=$NB_DIR( |\$)" || true
}

show() {   # $1 = port, $2 = url
    cat <<MSG

Your notebook server is running (crsid $CRSID, folder $NB_DIR):

    $2

To open it, on YOUR laptop run (and leave it open):

    ssh -L$1:localhost:$1 root@$HOST

then paste the URL above into your browser.
Log: $LOG    Stop it later with: bash setup/jupyter3.sh $CRSID stop
MSG
}

case $ACTION in
status)
    read -r port url < <(find_server) || true
    if [ -n "${url:-}" ]; then
        show "$port" "$url"
    else
        echo "No Python 3 notebook server is running for $CRSID. Start one with: bash setup/jupyter3.sh $CRSID"
    fi
    ;;

stop)
    read -r port url < <(find_server) || true
    if [ -z "${url:-}" ]; then
        echo "No Python 3 notebook server is running for $CRSID; nothing to stop."
        exit 0
    fi
    "$JUPYTER" server stop "$port" >>"$LOG" 2>&1 || true
    for _ in $(seq 1 15); do
        read -r port2 url2 < <(find_server) || true
        [ -z "${url2:-}" ] && break
        sleep 1
    done
    if [ -n "${url2:-}" ] || [ -n "$(server_pids)" ]; then
        die "the server on port $port did not stop; see $LOG and tell the course staff"
    fi
    echo "Stopped your notebook server (port $port). Your notebooks and results are untouched."
    ;;

start)
    # 1. already running?  -> just show it, start nothing.
    read -r port url < <(find_server) || true
    if [ -n "${url:-}" ]; then
        echo "Already running; nothing was started."
        show "$port" "$url"
        exit 0
    fi
    if [ -n "$(server_pids)" ]; then
        die "a notebook server process for $CRSID already exists (pid $(server_pids | tr '\n' ' ')) but is not answering yet. Nothing was started. Wait 10 s and run: bash setup/jupyter3.sh $CRSID status"
    fi

    # 2. take a per-crsid lock so two simultaneous starts cannot race,
    #    then re-check under the lock.
    exec 9>"$LOCK"
    if ! flock -n 9; then
        die "another 'jupyter3.sh $CRSID' is starting a server right now; wait a few seconds, then run: bash setup/jupyter3.sh $CRSID status"
    fi
    read -r port url < <(find_server) || true
    if [ -n "${url:-}" ] || [ -n "$(server_pids)" ]; then
        echo "Already running; nothing was started."
        [ -n "${url:-}" ] && show "$port" "$url"
        exit 0
    fi

    # 3. start it in the background (survives closing this terminal),
    #    bound to localhost only, and log to the crsid folder.
    echo "Starting your Python 3 notebook server (this takes a few seconds)..."
    printf '\n==== %s: started by jupyter3.sh %s ====\n' "$(date '+%F %T')" "$CRSID" >>"$LOG"
    nohup "$JUPYTER" notebook --allow-root --no-browser --ip 127.0.0.1 \
        --notebook-dir="$NB_DIR" >>"$LOG" 2>&1 9>&- &
    disown

    # 4. wait for it to register, then show the URL.
    for _ in $(seq 1 "$WAIT_SECS"); do
        sleep 1
        read -r port url < <(find_server) || true
        [ -n "${url:-}" ] && break
    done
    [ -n "${url:-}" ] || die "the server did not come up within $WAIT_SECS s. See the end of $LOG and tell the course staff."
    show "$port" "$url"
    ;;
esac
