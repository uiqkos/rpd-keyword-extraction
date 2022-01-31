import os
from functools import partial
from operator import attrgetter

from docx import Document as document
from docx.document import Document
from tqdm import tqdm as progressbar

from src.features.text_preprocessing import *
from src.features.utils import convert_doc_to_docx
from src.settings import DATA_PATH
from src.utils import list_files

os.environ['TIKA_JAVA'] = '"C:\\Program Files (x86)\\Java\\jre1.8.0_321\\bin\\java.exe"'

import tika

tika.initVM()
from tika import parser


def convert_to_text(exist_ignore=True):
    docs_path = DATA_PATH.joinpath('documents')
    texts_path = DATA_PATH.joinpath('texts')
    texts_path.mkdir(exist_ok=True)
    file_names = list_files(docs_path)

    if exist_ignore:
        text_names = list_files(texts_path)
        text_names = list(map(partial(re.sub, '.txt', ''), text_names))
        file_names = set(file_names).difference(text_names)

    for filename in progressbar(file_names, ncols=100):
        filepath = str(docs_path.joinpath(filename))

        if filename.endswith('.pdf') or filename.endswith('.PDF'):
            parsed = parser.from_file(filepath)
            text = parsed['content'] or ''

        elif filename.endswith('.doc'):
            docx_file_path = convert_doc_to_docx(filepath)
            doc: Document = document(docx_file_path)
            text = ' '.join(map(attrgetter('text'), doc.paragraphs))

        elif filename.endswith('.docx'):
            doc: Document = document(filepath)
            text = ' '.join(map(attrgetter('text'), doc.paragraphs))

        else:
            raise Exception('Unable to parse file: ' + filepath)

        processed_text = remove_stop_words(
            split(remove_numbers(text.lower()))
        )

        with open(texts_path.joinpath(filename + '.txt'), 'w', encoding='utf-8') as f:
            f.write(' '.join(processed_text))


if __name__ == '__main__':
    convert_to_text()
