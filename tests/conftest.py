import os
import sys

import pytest

os.environ.setdefault("MPLBACKEND", "Agg")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
USEFUL_DIR = os.path.join(REPO, "Jupyter", "useful")
NOTEBOOK_DIR = os.path.join(REPO, "Jupyter")
sys.path.insert(0, HERE)

from stage_fixtures import stage  # noqa: E402
from golden_dump import load_module, redirect_open  # noqa: E402

CRSID = "testcrsid"


@pytest.fixture(scope="session")
def lab_root(tmp_path_factory):
    """A staged /root/<crsid>/ tree built from the real result files."""
    root = str(tmp_path_factory.mktemp("labroot"))
    return stage(root)


@pytest.fixture(scope="session")
def crsid(lab_root):
    redirect_open(CRSID, lab_root)
    return CRSID


@pytest.fixture(scope="session")
def useful(crsid):
    """Namespace-like object with the ported helper modules loaded."""
    sys.path.insert(0, USEFUL_DIR)

    class NS:
        pass

    ns = NS()
    ns.u = load_module("useful", os.path.join(USEFUL_DIR, "useful.py"))
    ns.u1 = load_module("useful1", os.path.join(USEFUL_DIR, "useful1.py"))
    ns.u21 = load_module("useful2_1", os.path.join(USEFUL_DIR, "useful2.1.py"))
    ns.u22 = load_module("useful2_2", os.path.join(USEFUL_DIR, "useful2.2.py"))
    ns.u3 = load_module("useful3", os.path.join(USEFUL_DIR, "useful3.py"))
    return ns
