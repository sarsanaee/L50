# L50
Introduction to networking and systems measurements (L50) repository

## Getting started: running the notebooks (Python 3)

The lab notebooks run in **Python 3** with **Jupyter Notebook 7**, using a
self-contained installation on Machine A at `/opt/miniforge3/envs/l50`.
It is already installed; you do not install anything. Do not use the system
`python`, `python3` or `pip` on the lab machines for the notebooks, and do not
install packages into them.

**Note:** where the PDF handouts (`handouts/Intro.pdf`, `handouts/lab1.pdf`)
say `jupyter notebook --allow-root`, use the steps below instead. Everything
else in the handouts is unchanged.

### 1. Clone the repository on Machine A

Replace `<host>` with Machine A's hostname or IP and `<crsid>` with your crsid.
Several teams share the same root account, so everything of yours lives under
`/root/<crsid>`:

```
ssh root@<host>
mkdir -p /root/<crsid>
cd /root/<crsid>
git clone -b py3-jupyter7 https://github.com/sarsanaee/L50
cd L50
setup/mkdir1.sh <crsid>        # mkdir2.sh / mkdir3.sh for Labs 2 and 3
```

(`-b py3-jupyter7 .../sarsanaee/L50` is the Python 3 port of the notebooks;
once it is merged into https://github.com/cucl-srg/L50 a plain
`git clone https://github.com/cucl-srg/L50` is enough.)

### 2. Start the notebook server on Machine A

```
bash setup/jupyter3.sh <crsid>
```

It starts your server in the background and prints something like

```
Your notebook server is running (crsid <crsid>, folder /root/<crsid>/L50/Jupyter):

    http://127.0.0.1:8888/tree?token=0123abcd...

To open it, on YOUR laptop run (and leave it open):

    ssh -L8888:localhost:8888 root@<host>
```

Note the **port** (normally 8888; if another team's server is already using
it, yours gets the next free one, e.g. 8889) and keep the **token** URL.

The script is safe to run as many times as you like: if your server is
already running it just prints the URL again and starts nothing. It only ever
looks at the server for your own `/root/<crsid>/L50/Jupyter`, and never
touches other teams' servers or anything else on the machine. Two more forms:

```
bash setup/jupyter3.sh <crsid> status    # is it running? print the URL again
bash setup/jupyter3.sh <crsid> stop      # stop your server (notebooks and results are kept)
```

### 3. Open it in the browser on your own machine

In a **second** terminal on your laptop, forward the port Jupyter printed
(8888 below) to Machine A, and leave that terminal open too:

```
ssh -L8888:localhost:8888 root@<host>
```

Then paste the token URL from step 2 into your local browser. This is much
faster than running a browser on the lab machine over `ssh -X`. If you lose
the URL, `bash setup/jupyter3.sh <crsid> status` prints it again.

### 4. In the notebook

* Open the notebook for the experiment (e.g. `Lab1/Lab 1 Part 1 ping.ipynb`),
  fill in `crsid` and `machB_ip` in the first cell, and run cells with
  Shift+Enter. The first cell `%run`s the helper scripts in `Jupyter/useful/`.
* The kernel is **Python 3 (L50)** (menu *Kernel -> Change Kernel* shows it as
  `python3`). A `Python 2` kernel is also listed: that is the old stack and is
  only there as a fallback; do not use it for the current notebooks.
* Results are written under `/root/<crsid>/L50Lab<N>/` on Machine A. Back
  them up (`sftp root@<host>`, then `get -r <directory>`) and see
  `handouts/guide.ipynb` for notebook basics.

### Stopping and troubleshooting

* When you are done for the day, stop your server so ports and memory are
  free for other teams: `bash setup/jupyter3.sh <crsid> stop`. Closing the
  terminal does not stop it.
* A different port than expected: another team already had that port; use
  the port the script printed, and forward that one in step 3.
* Lost the token URL: `bash setup/jupyter3.sh <crsid> status`.
* `the Python 3 Jupyter stack is not installed`: tell the course staff (the
  install is `setup/install_py3_jupyter.sh`, run once per machine by staff; it
  touches nothing else on the system).
* `the server did not come up`: look at the end of `/root/<crsid>/jupyter3.log`
  and tell the course staff.
* A Python error mentioning `python3.5` or `distutils-precedence.pth` when you
  run *system* commands is unrelated to the notebooks and can be ignored.

Details of the Python 2 -> 3 port, the test suite and the installation are in
`MIGRATION.md`.
