import os


def list_files(path):
    return list(zip(*os.walk(path)))[2][0]


def identity(o):
    return o
