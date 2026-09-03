#!/usr/bin/env python3
"""Port the L50 lab notebooks from Python 2 to Python 3 in place.

Changes made (and nothing else):
  * kernelspec  python2 -> python3
  * `print x`   -> `print(x)`
  * the handful of integer divisions whose result is fed to a tool as an
    integer (OSNT ipg, tcpreplay pps, MoonGen count) or to matplotlib as a bin
    count: `/` -> `//` so the value stays an int as it was under Python 2
  * `% run` -> `%run` (stray space in Lab 3.2)

Run:  python3 tools/port_notebooks_py3.py [--check]
--check only reports what would change and exits 1 if anything would.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1] / "Jupyter"

PRINT_RE = re.compile(r"^(\s*)print (.+?)\s*$")

# exact-string substitutions, applied line by line
SUBS = [
    ("ipg = (10000/100)*(512+4+20)*8/10", "ipg = (10000//100)*(512+4+20)*8//10"),
    ("pps = 100000000 / ((512+4)*8)", "pps = 100000000 // ((512+4)*8)"),
    ("str(num/100)", "str(num//100)"),
    ("abs(maxx-minn)/2, (minn,maxx),log=True", "abs(maxx-minn)//2, (minn,maxx),log=True"),
    ("% run ", "%run "),
]

KERNELSPEC = {"display_name": "Python 3", "language": "python", "name": "python3"}
LANGUAGE_INFO = {"name": "python"}


def port_line(line):
    for old, new in SUBS:
        line = line.replace(old, new)
    m = PRINT_RE.match(line.rstrip("\n"))
    if m and not m.group(2).startswith("("):
        line = "%sprint(%s)%s" % (m.group(1), m.group(2), "\n" if line.endswith("\n") else "")
    return line


def port_notebook(path, check=False):
    nb = json.loads(path.read_text())
    changed = []
    for idx, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        src = cell["source"] if isinstance(cell["source"], list) else [cell["source"]]
        new = [port_line(l) for l in src]
        if new != src:
            changed.append(idx)
            cell["source"] = new
    meta = nb.setdefault("metadata", {})
    if meta.get("kernelspec") != KERNELSPEC or meta.get("language_info") != LANGUAGE_INFO:
        meta["kernelspec"] = KERNELSPEC
        meta["language_info"] = LANGUAGE_INFO
        changed.append("metadata")
    if changed and not check:
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
    return changed


def main():
    check = "--check" in sys.argv
    any_changed = False
    for nb in sorted(ROOT.glob("*/*.ipynb")):
        changed = port_notebook(nb, check)
        if changed:
            any_changed = True
            print("%s %s: cells %s" % ("would change" if check else "ported", nb.relative_to(ROOT), changed))
    if check and any_changed:
        sys.exit(1)


if __name__ == "__main__":
    main()
