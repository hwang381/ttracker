from sys import platform


def is_x11():
    return platform in ['linux', 'linux2']


def is_cocoa():
    return platform == 'darwin'
