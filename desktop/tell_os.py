import os
from sys import platform


def is_linux():
    return platform in ['linux', 'linux2']


def is_macos():
    return platform == 'darwin'


def is_win():
    return os.name == 'nt'
