"""Run every parsing/data function from Jupyter/useful/*.py over the staged
fixtures and print the results as JSON.

Runs under Python 2 (with the ORIGINAL useful modules) and Python 3 (with the
ported ones), so the two outputs can be diffed: that is the migration test.

Usage:
    python golden_dump.py <useful_dir> <crsid> [<staged_root>]

If <staged_root> is omitted, results are read from the real /root/<crsid>/
(use this on the lab machine: it also exercises getdeltas(), which shells out
to tshark). Otherwise open() is redirected from /root/<crsid>/ to
<staged_root>/ so the script can run anywhere.
"""
from __future__ import print_function
import json
import os
import sys

os.environ.setdefault("MPLBACKEND", "Agg")

PY2 = sys.version_info[0] == 2


def load_module(name, path):
    if PY2:
        import imp
        return imp.load_source(name, path)
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def redirect_open(crsid, staged_root):
    if PY2:
        import __builtin__ as builtins
    else:
        import builtins
    real_open = builtins.open
    prefix = "/root/" + crsid + "/"

    def fake_open(path, *a, **k):
        if isinstance(path, str) and path.startswith(prefix):
            path = os.path.join(staged_root, path[len(prefix):])
        return real_open(path, *a, **k)

    builtins.open = fake_open


def tolist(x):
    """numpy scalars/arrays -> plain python for JSON."""
    if hasattr(x, "tolist"):
        return x.tolist()
    if isinstance(x, (list, tuple)):
        return [tolist(i) for i in x]
    return x


def dump(useful_dir, crsid, staged_root=None):
    sys.path.insert(0, useful_dir)
    if staged_root:
        redirect_open(crsid, staged_root)
    u1 = load_module("useful1", os.path.join(useful_dir, "useful1.py"))
    u21 = load_module("useful2_1", os.path.join(useful_dir, "useful2.1.py"))
    u22 = load_module("useful2_2", os.path.join(useful_dir, "useful2.2.py"))
    u3 = load_module("useful3", os.path.join(useful_dir, "useful3.py"))

    out = {}
    out["getrtt_1a"] = u1.getrtt("1/exp1a_0", crsid, 1000)
    out["getrtts_1a_0"] = u1.getrtts("1/exp1a", crsid, 1000)[0]
    out["getrtt_2a_0.001"] = u1.getrtt("2/exp2a_0.001", crsid, 500)
    out["getrtt_5a"] = u1.getrtt("5/exp5a_0.001_1_0", crsid, 100)
    out["data_iperf_9"] = u1.data_iperf("9/exp9", crsid)
    out["data10"] = u1.data10(crsid)
    out["data11"] = u1.data11([50], crsid)
    out["data_band_12"] = u1.data_band("12/exp12", crsid, [100])
    out["data_iperf_13a"] = u1.data_iperf("13/exp13a", crsid)
    out["data13b"] = u1.data13b([50], crsid)
    out["data_band_13c"] = u1.data_band("13/exp13c", crsid, [100])
    out["graph_error_9"] = u1.graph_error(out["data_iperf_9"])
    out["ind_of"] = [u1.ind_of(v, out["getrtt_1a"]) for v in (0.0, 82.0, 100.0, 1e9)]
    out["gettimes_2.1"] = u21.gettimes("exp1a", crsid)
    out["gettimes_2.2"] = u22.gettimes("exp2a_0", crsid)
    # getrtt() prints progress lines; silence them
    devnull = open(os.devnull, "w")
    real_stdout, sys.stdout = sys.stdout, devnull
    try:
        out["getrtt_2.2_dag"] = u22.getrtt("exp2e_dag_filtered.txt", crsid)
        out["getrtt_2.2_tcpdump"] = u22.getrtt("exp2e_tcpdump.txt", crsid)
    finally:
        sys.stdout = real_stdout
    if staged_root is None and os.system("which tshark >/dev/null 2>&1") == 0:
        out["getdeltas_3.2_2a"] = u3.getdeltas("3.2/exp2a", crsid, 1000)
    return dict((k, tolist(v)) for k, v in out.items())


if __name__ == "__main__":
    useful_dir, crsid = sys.argv[1], sys.argv[2]
    staged = sys.argv[3] if len(sys.argv) > 3 else None
    json.dump(dump(useful_dir, crsid, staged), sys.stdout, indent=1, sort_keys=True)
    print()
