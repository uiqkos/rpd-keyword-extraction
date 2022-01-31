import os
import re
from operator import indexOf, attrgetter
from typing import Union, Iterable, List

import numpy as np
import pdf2docx
from docx.table import Table
from win32com import client as wc


def convert_doc_to_docx(filepath, remove=False):
    w = wc.Dispatch('Word.Application')
    doc = w.Documents.Open(filepath)
    doc.SaveAs(filepath + 'x', 16)
    if remove:
        os.remove(filepath)
    return filepath + 'x'


def convert_pdf_to_docx(filepath, remove=False):
    cv = pdf2docx.Converter(filepath)
    new_filepath = filepath.replace('.pdf', '.docx').replace('.PDF', '.docx')
    cv.convert(new_filepath, start=0, end=None)
    cv.close()
    if remove:
        os.remove(filepath)
    return new_filepath


def fix_column(column: Iterable[Union[str, type(np.nan)]]) -> List[str]:
    buffer = []
    items = []

    def release_buffer():
        if buffer:
            items.append(' '.join(map(str, buffer)))
            buffer.clear()

    for item in column:
        if item is np.nan:
            release_buffer()

        else:
            buffer.append(item)

    release_buffer()
    return items


def process(s):
    return ' '.join(re.findall(r'\w+', str(s).lower()))


def contains_marker(container, marker) -> Union[bool, type(None)]:
    marker = process(marker)

    def match(s): return (s := process(s)) in marker or marker in s

    # try:
    #     idx = indexOf(list(map(match, container)), True)
    #
    # except ValueError:
    #     idx = None

    return any(map(match, container))


def table_to_columns(table: Table) -> List[List[str]]:
    return [list(map(attrgetter('text'), column.cells)) for column in table.columns]
