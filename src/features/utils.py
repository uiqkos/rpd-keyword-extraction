import os
import re
from operator import indexOf

import pdf2docx
from docx2pdf import convert
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


def convert_docx_to_pdf(filepath, remove=False):
    filepath = str(filepath)
    convert(filepath, (new_filepath := filepath.replace('.docx', '.pdf')))
    return new_filepath


def process(s):
    return ' '.join(re.findall(r'\w+', str(s).lower()))


def index_of_marker(container, marker) -> int:
    marker = process(marker)

    def match(s): return process(s) == marker

    try:
        idx = indexOf(list(map(match, container)), True)

    except ValueError:
        idx = -1

    return idx
