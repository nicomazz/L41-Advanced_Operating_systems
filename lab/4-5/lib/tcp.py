import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
from collections import defaultdict
from dtrace import *


def dummy_f(cmd):
    return "Don't forget to call set_exec_callback from the jupyter notebook!"


cmd = dummy_f


def set_tcp_exec_callback(c):
    global cmd
    cmd = c


def set_latency(latency=10):
    cmd("ipfw pipe config 1 delay {}".format(str(latency)))
    cmd("ipfw pipe config 2 delay {}".format(str(latency)))


def setup_pipes(latency=10):
    set_latency(latency)
    cmd("ifconfig lo0 mtu 1500")
    cmd("ipfw add 1 pipe 1 tcp from any 10141 to any via lo0")
    cmd("ipfw add 2 pipe 2 tcp from any to any 10141 via lo0")
