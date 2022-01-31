import re
from operator import indexOf
from typing import Union, Iterable, List

import numpy as np
from win32com import client as wc


def convert_doc_to_docx(filepath):
    w = wc.Dispatch('Word.Application')
    doc = w.Documents.Open(filepath)
    doc.SaveAs(filepath + 'x', 16)
    return filepath + 'x'


def convert_pdf_to_docx(filepath):



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

    try:
        idx = indexOf(list(map(match, container)), True)

    except ValueError:
        idx = None

    return idx
