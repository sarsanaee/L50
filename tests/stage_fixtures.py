"""Build a fake /root/<crsid>/ results tree from the small set of real result
files in tests/fixtures.

The helper functions expect N repetitions of each experiment (exp1a_0..9,
exp9_0..4, ...). We only keep one real file per experiment type in the repo and
replicate it across the expected indices; the point is to exercise the parsers
on real tool output, not to reproduce a full run.

Works under both Python 2 and Python 3 so that golden outputs can be produced
on the lab machine with the original interpreter.
"""
from __future__ import print_function
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")

# (fixture file, [staged names])
LAYOUT = [
    ("L50Lab1/1/exp1a_0", ["L50Lab1/1/exp1a_%d" % i for i in range(10)]),
    ("L50Lab1/1/exp1b_0", ["L50Lab1/1/exp1b_%d" % i for i in range(10)]),
    ("L50Lab1/2/exp2a_0.001", ["L50Lab1/2/exp2a_0.001", "L50Lab1/2/exp2b_0.001"]),
    ("L50Lab1/5/exp5a_0.001_1_0",
     ["L50Lab1/5/exp5a_%s_%d_%d" % (iv, u, i) for iv in ("0.001", "0.000001") for u in (1, 5) for i in range(10)]),
    ("L50Lab1/9/exp9_0", ["L50Lab1/9/exp9_%d" % i for i in range(5)]),
    ("L50Lab1/10/exp10_0", ["L50Lab1/10/exp10_%d" % i for i in range(5)]),
    ("L50Lab1/11/exp11_50_0", ["L50Lab1/11/exp11_50_%d" % i for i in range(5)]),
    ("L50Lab1/12/exp12_100_0", ["L50Lab1/12/exp12_100_%d" % i for i in range(5)]),
    ("L50Lab1/13/exp13a_0", ["L50Lab1/13/exp13a_%d" % i for i in range(5)]),
    ("L50Lab1/13/exp13b_50_0", ["L50Lab1/13/exp13b_50_%d" % i for i in range(5)]),
    ("L50Lab1/13/exp13c_100_0", ["L50Lab1/13/exp13c_100_%d" % i for i in range(5)]),
    ("L50Lab2/2.1/exp1a.txt", ["L50Lab2/2.1/exp1a.txt"]),
    ("L50Lab2/2.2/exp2a_0.txt", ["L50Lab2/2.2/exp2a_0.txt"]),
    ("L50Lab2/2.2/exp2e_dag_filtered.txt", ["L50Lab2/2.2/exp2e_dag_filtered.txt"]),
    ("L50Lab2/2.2/exp2e_tcpdump.txt", ["L50Lab2/2.2/exp2e_tcpdump.txt"]),
    ("L50Lab3/3.2/exp2a.txt", ["L50Lab3/3.2/exp2a.txt"]),
    ("L50Lab3/3.2/exp2a.erf", ["L50Lab3/3.2/exp2a.erf"]),
    ("L50Lab3/3.2/exp2c3_d.txt", ["L50Lab3/3.2/exp2c3_d.txt"]),
]


def stage(root):
    """Populate `root` (which plays the role of /root/<crsid>) and return it."""
    for src, dests in LAYOUT:
        s = os.path.join(FIXTURES, src)
        if not os.path.exists(s):
            continue
        for d in dests:
            dpath = os.path.join(root, d)
            ddir = os.path.dirname(dpath)
            if not os.path.isdir(ddir):
                os.makedirs(ddir)
            shutil.copyfile(s, dpath)
    return root


if __name__ == "__main__":
    import sys
    print(stage(sys.argv[1]))
