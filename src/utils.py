import os


def file_names_in(path):
    return list(zip(*os.walk(path)))[2][0]


def identity(o):
    return o
