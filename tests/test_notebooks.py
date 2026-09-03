"""Static checks on the ported notebooks plus execution of the analysis
functions they define, against the staged fixture data."""
import glob
import json
import os
import re
import subprocess
import sys

import pytest
from IPython.core.inputtransformer2 import TransformerManager

from conftest import NOTEBOOK_DIR, REPO

NOTEBOOKS = sorted(glob.glob(os.path.join(NOTEBOOK_DIR, "*", "*.ipynb")))
assert len(NOTEBOOKS) == 8


def code_cells(path):
    nb = json.load(open(path))
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] == "code":
            yield i, "".join(c["source"])


@pytest.mark.parametrize("nb", NOTEBOOKS, ids=os.path.basename)
def test_kernelspec_is_python3(nb):
    meta = json.load(open(nb))["metadata"]
    assert meta["kernelspec"]["name"] == "python3"
    assert meta["kernelspec"]["language"] == "python"


@pytest.mark.parametrize("nb", NOTEBOOKS, ids=os.path.basename)
def test_every_code_cell_compiles_under_python3(nb):
    tm = TransformerManager()
    for i, src in code_cells(nb):
        py = tm.transform_cell(src)          # expands %magics / !shell as IPython would
        compile(py, "%s[cell %d]" % (os.path.basename(nb), i), "exec")


@pytest.mark.parametrize("nb", NOTEBOOKS, ids=os.path.basename)
def test_no_python2_print_statements(nb):
    for i, src in code_cells(nb):
        for line in src.splitlines():
            assert not re.match(r"^\s*print [^(]", line), "%s cell %d: %s" % (nb, i, line)


def test_port_script_is_idempotent():
    r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "port_notebooks_py3.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_integer_parameters_stay_integers():
    """Values handed to OSNT / tcpreplay / MoonGen on the command line were ints
    under Python 2; make sure the ported expressions still are."""
    lab31 = open(glob.glob(os.path.join(NOTEBOOK_DIR, "Lab3", "Lab 3.1*"))[0]).read()
    lab32 = open(glob.glob(os.path.join(NOTEBOOK_DIR, "Lab3", "Lab 3.2*"))[0]).read()
    lab33 = open(glob.glob(os.path.join(NOTEBOOK_DIR, "Lab3", "Lab 3.3*"))[0]).read()
    assert "ipg = (10000//100)*(512+4+20)*8//10" in lab31
    assert eval("(10000//100)*(512+4+20)*8//10") == 42880
    assert "pps = 100000000 // ((512+4)*8)" in lab32
    assert eval("100000000 // ((512+4)*8)") == 24224
    assert "str(num//100)" in lab33


def _nb_function(nb_glob, name):
    """Extract `def name(...)` (up to the next top-level statement) from a notebook."""
    path = glob.glob(os.path.join(NOTEBOOK_DIR, "*", nb_glob))[0]
    for _, src in code_cells(path):
        if ("def %s(" % name) in src:
            lines, keep = src.splitlines(), []
            for line in lines[lines.index(next(l for l in lines if l.startswith("def %s(" % name))):]:
                if keep and line and not line[0].isspace():
                    break
                keep.append(line)
            return "\n".join(keep)
    raise AssertionError("%s not found in %s" % (name, nb_glob))


def test_notebook_defined_graph_functions_run(useful, crsid):
    """graph2 (Lab 1), rtt_graph (Lab 2.2) and rate (Lab 3.2) are defined inside
    the notebooks; exec them exactly as written against the fixtures."""
    import matplotlib.pyplot as plt

    # each notebook %run's useful.py plus exactly one lab-specific helper
    def notebook_ns(helper):
        ns = dict(vars(useful.u))
        ns.update(vars(helper))
        ns["crsid"] = crsid
        return ns

    ns1 = notebook_ns(useful.u1)
    exec(_nb_function("Lab 1 Part 1*", "graph2"), ns1)
    ns1["graph2"]("exp2a", ["0.001"], 500)

    ns22 = notebook_ns(useful.u22)
    exec(_nb_function("Lab 2.2*", "rtt_graph"), ns22)
    rtt = useful.u22.getrtt("exp2e_dag_filtered.txt", crsid)
    ns22["rtt_graph"](rtt)          # bins argument must be an int: uses // after the port

    exec(_nb_function("Lab 2.2*", "cmp_ports"), ns22)
    # synthetic slf0-slf1 timestamp differences spanning +-500 us, like real runs
    ns22["getdiff"] = lambda exp, crsid: [float(i % 1000) - 500 for i in range(100000)]
    ns22["cmp_ports"]("exp2b")
    plt.close("all")
