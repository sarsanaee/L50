from subprocess import Popen, PIPE
import matplotlib.pyplot as plt
import shlex
from time import sleep, strptime
import numpy as np
from numpy import average
import paramiko
from _thread import start_new_thread
from re import findall
from math import ceil, floor

def local_cmd(command):
    # universal_newlines=True makes stdout a text stream (str), as it was in Python 2
    stdout = Popen(command, shell=True, stdout=PIPE, universal_newlines=True).stdout
    return stdout.read()

def ssh_connect(host):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host)
    return ssh

def ssh_cmd(command, ssh):
    output = ""
    stdout = ssh.exec_command(command)[1]
    for line in stdout:
        output += line
    if (len(output) > 0):
        return output
