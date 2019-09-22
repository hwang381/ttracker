from sys import platform


def is_linux():
    return platform in ['linux', 'linux2']


def is_macos():
    return platform == 'darwin'
