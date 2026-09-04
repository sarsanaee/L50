# L50: Python 2 -> Python 3 and Jupyter Notebook 7 migration

Scope: the student-facing stack only, i.e. the Jupyter server, the kernel the
notebooks run in, and the code in `Jupyter/`. Not in scope and not touched:
the OS (Ubuntu 16.04), the kernel, DAG tools/driver, OSNT/NetFPGA tooling
(`osnt-tool-cmd.py` stays Python 2 on machine B and is only invoked over ssh),
MoonGen, tcpreplay, tshark.

## What breaks under Python 3 (findings)

Everything in `Jupyter/` was audited: 5 helper modules (344 lines) and 8
notebooks (~590 lines of code cells). The breakage is small and mechanical.

| # | Where | Problem | Effect under py3 | Fix |
|---|-------|---------|------------------|-----|
| 1 | `useful.py` | `from thread import start_new_thread` | ImportError on the first cell of every notebook | `from _thread import ...` |
| 2 | `useful.py` `local_cmd` | `Popen(...).stdout.read()` returns `bytes` | `print(local_cmd(...))` shows `b'...'`; string concatenation fails | `universal_newlines=True` |
| 3 | `useful1.py`, `useful2.1.py`, `useful2.2.py`, `useful3.py` | `f.next()` (23 occurrences) | AttributeError in every parser | `next(f)` |
| 4 | `useful1.py` `data_band`, `graph_error` | `map(...)` is lazy | `meds[i]` -> TypeError; notebooks do `ys.append(ys[-1])` on the result | `list(map(...))` |
| 5 | `useful2.2.py` | tabs mixed with spaces | TabError at import (py2 tolerated it) | re-indent with spaces |
| 6 | `useful2.2.py` + 22 notebook cells | `print x` statements | SyntaxError | `print(x)` |
| 7 | Lab 3.1 cells 27, 34 | `ipg = (10000/100)*(512+4+20)*8/10` | `42880.0` instead of `42880`, passed as `-ipg0 42880.0` to the OSNT CLI | `//` |
| 8 | Lab 3.2 cell 27 | `pps = 100000000 / ((512+4)*8)` | `24224.8...` instead of `24224` passed to `tcpreplay -p` | `//` |
| 9 | Lab 3.3 cell 4 | `str(num/100)` | `"10.0"` instead of `"10"` passed to the MoonGen Lua script | `//` |
| 10 | Lab 2.2 cells 13, 29 | `plt.hist(x, abs(maxx-minn)/2, ...)` | matplotlib rejects a float bin count | `//` |
| 11 | Lab 3.2 cell 2 | `% run` (stray space) | harmless, normalised | `%run` |
| 12 | all notebooks | kernelspec `python2` | notebook would not open under the new kernel | kernelspec `python3` |

Everything else (numpy histogram/cumsum, matplotlib `errorbar`/`step`/`hist`
positional arguments, paramiko `SSHClient` usage, `%%capture`, `!shell` cells,
`shlex`/`Popen` capture control) works unchanged on numpy 2.5, matplotlib
3.11, paramiko 5.0 and IPython 9, as verified by the test suite.

Non-Python things that do *not* change: fixed-column slicing of tshark output
(`[42:53]`, `[46:57]`) depends on the tshark version, not Python; the ssh key
used for A->B is RSA 2048 (paramiko >= 3 dropped DSA only).

## What was changed in this branch

* `Jupyter/useful/*.py`: minimal port, same function names and signatures.
* `Jupyter/*/*.ipynb`: ported by `tools/port_notebooks_py3.py` (re-runnable,
  `--check` mode for CI). Only the lines in the table above and the kernel
  metadata differ; markdown/instructions are untouched.
* `tests/`: pytest suite (see below).
* `setup/install_py3_jupyter.sh`: installs the new stack on machine A.

## Tests

```
python3 -m venv .venv && .venv/bin/pip install pytest numpy matplotlib paramiko ipykernel
.venv/bin/python -m pytest tests
```

* `tests/fixtures/` holds real result files captured on the lab machines
  (ping, iperf, iperf3, tshark, DAG). `stage_fixtures.py` replicates them into
  the `/root/<crsid>/L50LabN/...` layout the helpers expect.
* `test_useful.py`: every parser on real tool output, plus the graph functions
  on current matplotlib (Agg backend).
* `test_notebooks.py`: every code cell compiles under Python 3 after IPython
  magic transformation; no `print` statements remain; kernelspec is python3;
  the integer command-line parameters stay integers; the analysis functions
  defined inside the notebooks (`graph2`, `rtt_graph`, `cmp_ports`) run.
* Differential test against the Python 2 originals: on machine A run

  ```
  python2 tests/golden_dump.py /root/<crsid>/L50/Jupyter/useful <crsid> <staged>  > tests/golden_py2.json
  ```

  with the *original* helpers, then `pytest` compares the ported helpers'
  output with it (`test_golden_matches_python2_originals`, skipped until the
  file exists).

## Installing the new stack on the lab machine (on the cloned disk)

Ubuntu 16.04 has OpenSSL 1.0.2 and glibc 2.23. Current Jupyter Notebook
(7.6) needs Python >= 3.10, and CPython >= 3.10 needs OpenSSL >= 1.1.1 for
its ssl module, so building CPython from source there gives a Python without
working pip/https. Miniforge (conda-forge) ships its own OpenSSL and only
needs glibc >= 2.17, so it is the route that touches nothing on the system:

```
bash setup/install_py3_jupyter.sh <crsid>
/opt/miniforge3/envs/l50/bin/jupyter notebook --allow-root --no-browser --notebook-dir=/root/<crsid>/L50/Jupyter
```

This leaves `/usr/local/bin/jupyter` (Notebook 5.7, Python 2) intact and
keeps the `python2` kernelspec visible in the new server as a fallback.

## Status on nf-test105 (done 2026-09-04, on the cloned OS disk)

* Installed: Python 3.12.14, Notebook 7.6.2, jupyter_server 2.21, ipykernel
  7.3, IPython 9.17, numpy 2.5.2, matplotlib 3.10.9, paramiko 5.0.0 in
  `/opt/miniforge3/envs/l50`. System python2/python3.5, Jupyter 5.7, DAG and
  OSNT untouched.
* `/root/ss3230/L50` is now the ported branch (`py3-jupyter7`); the original
  Python 2 checkout is kept at `/root/ss3230/L50-py2-orig`.
* All 38 tests pass on the machine under the new env, including the tshark
  test and the differential test against Python 2 (`tests/golden_py2.json`,
  generated there with python2 + the original helpers).
* Notebook 7 drives both kernels (verified by executing cells through
  nbclient). **Gotcha fixed:** the legacy kernelspec
  `/usr/local/share/jupyter/kernels/python2/kernel.json` used a bare `python`,
  which resolves to the *new* Python 3 when launched from the new server; it
  now points to `/usr/bin/python2` (backup: `kernel.json.orig`).
* `%run` of `useful*.py` from the new IPython resolves `from useful import`.
* Start the server (already running on port 8888, log `/root/ss3230/jupyter7.log`):

  ```
  /opt/miniforge3/envs/l50/bin/jupyter notebook --allow-root --no-browser --port 8888 --ip 127.0.0.1 --notebook-dir=/root/ss3230/L50/Jupyter
  ```

  then from the laptop `ssh -L8888:localhost:8888 root@nf-test105...` and open the token URL from the log.

Still to verify: live runs of the Lab 2/3 `send()` cells with the `//` values
(needs fibres and the NetFPGA bitstream), and a student-style walk through each
notebook in the browser.
