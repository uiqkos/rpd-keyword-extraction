import os
import re
import warnings
from functools import reduce, partial, wraps
from operator import indexOf
from typing import Iterator

import xlrd
import csv
import pdf2docx
from docx2pdf import convert
from tqdm import tqdm
from win32com import client as wc

from src.settings import DATA_PATH

progressbar = partial(tqdm, ncols=100)


def convert_doc_to_docx(filepath, remove=False):
    w = wc.Dispatch('Word.Application')
    doc = w.Documents.Open(filepath)
    new_filepath = filepath
    new_filepath.name += 'x'
    doc.SaveAs(new_filepath, 16)

    if remove:
        os.remove(filepath)

    return new_filepath


def convert_pdf_to_docx(filepath, remove=False):
    cv = pdf2docx.Converter(filepath)
    new_filepath = filepath.replace('.pdf', '.docx').replace('.PDF', '.docx')
    cv.convert(new_filepath, start=0, end=None)
    cv.close()
    if remove:
        os.remove(filepath)
    return new_filepath


def convert_docx_to_pdf(filepath, remove=False):
    new_filepath = filepath
    new_filepath.name = new_filepath.replace('.docx', '.pdf')
    convert(filepath, new_filepath)

    return new_filepath


def convert_xlsx_to_csv(filepath):
    wb = xlrd.open_workbook(filepath)
    sh = wb.sheet_by_name('Sheet1')
    new_filepath = filepath
    new_filepath.name = new_filepath.name.replace('.xlsx', '.csv')

    with open(new_filepath, 'w') as csv_file:
        wr = csv.writer(csv_file, quoting=csv.QUOTE_ALL)
        wr.writerows(sh.get_rows())


def process(s):
    return ' '.join(re.findall(r'\w+', str(s).lower()))


def index_of_marker(container, marker) -> int:
    marker = process(marker)

    def match(s):
        return process(s) == marker

    try:
        idx = indexOf(list(map(match, container)), True)

    except ValueError:
        idx = -1

    return idx


def file_names(path):
    return list(zip(*os.walk(path)))[2][0]


def file_paths(path) -> Iterator[os.PathLike]:
    return map(path.joinpath, file_names(path))


def identity(o):
    return o


def compose2(f1, f2):
    return lambda *args, **kwargs: f2(f1(*args, **kwargs))


def compose(*fs):
    return reduce(compose2, fs)


def and_2predicates(p1, p2):
    return lambda *args, **kwargs: p1(*args, **kwargs) and p2(*args, **kwargs)


def and_predicates(*ps):
    return reduce(and_2predicates, ps)


def tupled(f):
    @wraps(f)
    def wrapper(tup):
        return f(*tup)

    return wrapper
