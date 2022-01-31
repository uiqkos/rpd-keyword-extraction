import os
from functools import partial
from operator import attrgetter

from docx import Document as document
from docx.document import Document
from tqdm import tqdm as progressbar
from win32com import client as wc

from src.features.text_preprocessing import *
from src.settings import DATA_PATH
from src.utils import file_names_in

os.environ['TIKA_JAVA'] = '"C:\\Program Files (x86)\\Java\\jre1.8.0_321\\bin\\java.exe"'

import tika

tika.initVM()
from tika import parser


def convert_to_text(exist_ignore=True):
    docs_path = DATA_PATH.joinpath('documents')
    texts_path = DATA_PATH.joinpath('texts')
    texts_path.mkdir(exist_ok=True)
    file_names = file_names_in(docs_path)

    if exist_ignore:
        text_names = file_names_in(texts_path)
        text_names = list(map(partial(re.sub, '.txt', ''), text_names))
        file_names = set(file_names).difference(text_names)

    for file_name in progressbar(file_names, ncols=100):
        file_path = str(docs_path.joinpath(file_name))

        if file_name.endswith('.pdf') or file_name.endswith('.PDF'):
            parsed = parser.from_file(file_path)
            text = parsed['content'] or ''

        elif file_name.endswith('.doc'):
            w = wc.Dispatch('Word.Application')
            doc = w.Documents.Open(file_path)
            doc.SaveAs(file_path + 'x', 16)

            doc: Document = document(file_path + 'x')
            text = ' '.join(map(attrgetter('text'), doc.paragraphs))

        elif file_name.endswith('.docx'):
            doc: Document = document(file_path)
            text = ' '.join(map(attrgetter('text'), doc.paragraphs))

        else:
            raise Exception('Unable to parse file: ' + file_path)

        processed_text = remove_stop_words(
            split(remove_numbers(text.lower()))
        )

        with open(texts_path.joinpath(file_name + '.txt'), 'w', encoding='utf-8') as f:
            f.write(' '.join(processed_text))


if __name__ == '__main__':
    convert_to_text()
