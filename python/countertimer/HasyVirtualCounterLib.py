#!/usr/bin/env python
# import sys

# import taurus
# import PyTango

# import time

valor = 0


def reset(case):
    global valor
    if case == 1:
        valor = 0
    elif case == 2:
        valor = 10


def myread(case):
    global valor
    if case == 1:
        valor = valor + 1
    elif case == 2:
        valor = valor - 1
    return valor
