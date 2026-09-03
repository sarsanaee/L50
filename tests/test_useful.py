"""Tests for the ported Jupyter/useful/*.py helpers under Python 3 with
current numpy / matplotlib / paramiko.

Two layers:
  1. behavioural checks against known values in the real fixture files;
  2. differential check: identical output to the Python 2 originals, using
     tests/golden_py2.json produced on the lab machine with
        python2 tests/golden_dump.py <orig useful dir> <crsid> <staged root>
     (skipped until that file exists).
"""
import json
import os
import subprocess
import sys

import numpy as np
import pytest

from conftest import HERE, USEFUL_DIR
from golden_dump import dump

GOLDEN = os.path.join(HERE, "golden_py2.json")


def test_imports_have_no_python2_leftovers(useful):
    # `thread` module and iterator .next() were the two hard import/runtime breaks
    import _thread  # noqa: F401
    assert useful.u.start_new_thread is _thread.start_new_thread
    for mod in (useful.u1, useful.u21, useful.u22, useful.u3):
        src = open(mod.__file__).read()
        assert ".next()" not in src, mod.__file__
        assert "\t" not in src, "tabs would be a TabError under py3: %s" % mod.__file__


def test_local_cmd_returns_text_not_bytes(useful):
    out = useful.u.local_cmd("echo hello")
    assert isinstance(out, str)
    assert out == "hello\n"


def test_getrtt_parses_ping_output(useful, crsid):
    rtt = useful.u1.getrtt("1/exp1a_0", crsid, 1000)
    assert len(rtt) == 1000
    assert rtt == sorted(rtt)
    # first three lines of the fixture are 0.112, 0.106, 0.082 ms -> microseconds
    assert 82.0 in rtt and 106.0 in rtt and 112.0 in rtt
    assert min(rtt) > 0


def test_getrtts_replicates_across_runs(useful, crsid):
    rtts = useful.u1.getrtts("1/exp1a", crsid, 1000)
    assert len(rtts) == 10 and all(len(r) == 1000 for r in rtts)


def test_data_iperf_and_graph_error_return_lists(useful, crsid):
    bws = useful.u1.data_iperf("9/exp9", crsid)
    assert len(bws) == 10 and all(len(b) == 5 for b in bws)
    meds, minsmaxs = useful.u1.graph_error(bws)
    # map() must have been materialised: the notebooks call ys.append(ys[-1])
    assert isinstance(meds, list)
    meds.append(meds[-1])
    assert len(minsmaxs[0]) == 10


def test_data10_data11_data13b(useful, crsid):
    sbw, cbw = useful.u1.data10(crsid)
    assert len(sbw) == 10 and len(cbw) == 10
    winds, bws = useful.u1.data11([50], crsid)
    assert winds == [100.0]          # 'TCP window size:  100 KByte' -> cols 17:21
    assert len(bws[0]) == 5 and bws[0][0] == pytest.approx(5.853068)
    bws13 = useful.u1.data13b([50], crsid)
    assert len(bws13[0]) == 5


def test_data_band_returns_list_of_floats(useful, crsid):
    bans, pcs = useful.u1.data_band("12/exp12", crsid, [100])
    assert isinstance(bans, list)      # was a lazy map() in py3 before the port
    assert bans[0] == pytest.approx(101.0)
    assert pcs[0] == [0.0] * 5


def test_lab2_parsers(useful, crsid):
    times = useful.u21.gettimes("exp1a", crsid)
    assert len(times) == 1000 and times[0] == "0.000000000"
    lines = useful.u22.gettimes("exp2a_0", crsid)
    assert len(lines) == 1000
    rtt = useful.u22.getrtt("exp2e_dag_filtered.txt", crsid)
    assert len(rtt) == 10000 and all(isinstance(x, float) for x in rtt)


@pytest.mark.skipif(subprocess.call("which tshark >/dev/null 2>&1", shell=True) != 0,
                    reason="tshark not installed")
def test_getdeltas_shells_out_to_tshark(useful, crsid, lab_root, monkeypatch):
    # getdeltas builds the tshark command with the literal /root/<crsid>/ path,
    # so run it through a shim that rewrites that prefix to the staged root.
    orig = useful.u.local_cmd
    monkeypatch.setattr(useful.u3, "local_cmd",
                        lambda c: orig(c.replace("/root/" + crsid + "/", lab_root + "/")))
    deltas = useful.u3.getdeltas("3.2/exp2a", crsid, 1000)
    assert len(deltas) == 999
    assert all(d >= 0 for d in deltas)


def test_graph_functions_run_on_current_matplotlib(useful, crsid):
    import matplotlib.pyplot as plt
    useful.u1.graph1("exp1a", crsid, 10.0, 1000)
    useful.u1.graph5_001("exp5a", crsid, [1, 5], 100)
    useful.u1.graph5_000001("exp5a", crsid, [1, 5], 100)
    plt.close("all")


def test_golden_matches_python2_originals(crsid, lab_root):
    if not os.path.exists(GOLDEN):
        pytest.skip("tests/golden_py2.json not generated yet (run golden_dump.py with python2 on the lab machine)")
    golden = json.load(open(GOLDEN))
    got = dump(USEFUL_DIR, crsid, lab_root)
    for key in sorted(set(golden) & set(got)):
        assert got[key] == golden[key], key
    missing = set(golden) - set(got)
    assert not missing - {"getdeltas_3.2_2a"}, missing
