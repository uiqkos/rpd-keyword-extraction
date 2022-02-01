import logging
import os
import re
import string
from functools import partial, reduce
from pathlib import Path

from packaging import markers

os.environ['LD_LIBRARY_PATH'] = 'C:\\Program Files\\gs\\gs9.55.0\\bin\\gsdll64.dll'
logging.disable()

from itertools import filterfalse
from dataclasses import dataclass
from os import PathLike
from typing import List, Iterator, Set, Tuple, Dict

import camelot
import pandas as pd
from pikepdf import Pdf
from tqdm import tqdm as progressbar

from src.features.utils import convert_doc_to_docx, process, convert_pdf_to_docx, index_of_marker, convert_docx_to_pdf
from src.settings import DATA_PATH
from src.utils import list_files


MARKERS = (
    'Планируемые результаты обучения',
    'Наименование раздела дисциплины',
    'Наименование раздела дисциплины (модуля)',
    'Содержание',

    # ГИА
    'Наименование оценочного средства',
)


def clean_keyword(word):
    word = re.sub(r'\n', '', word)
    word = re.sub(r'\w+ (\d\. ?)+', '', word)
    word = re.sub(r'\(.*\)', '', word)
    word = re.sub(r' ?[-–●•] ', '', word)
    # word = re.sub('Умения:', ' ', word)
    # word = re.sub('Навыки:', ' ', word)
    # word = re.sub('Знания:', ' ', word)
    # word = re.sub('Итого:', ' ', word)
    word = re.sub(r'\w+:', '', word)
    word = re.sub(' +', ' ', word)
    word = word.strip()

    return word


def indexes_of(string: str, substring: str):
    indexes = []
    try:
        while True:
            indexes.append(string.index(substring, (indexes[-1] if indexes else -1) + 1))
    except ValueError:
        return indexes


def split(word: str):
    seqs = set()
    buffer = []

    def release_buffer():
        if buffer:
            seqs.add(''.join(buffer))
            buffer.clear()

    for c in word:
        if c in ('.', ',', ';'):
            release_buffer()
        # elif c == c.upper() and c != ' ' and (buffer and buffer[-1] != buffer[-1].upper()):
        #     release_buffer()
        #     buffer.append(c)
        elif buffer or c != ' ':
            buffer.append(c)
    release_buffer()

    return seqs


@dataclass
class Extractor:
    markers: Tuple[str, ...]

    def extract(self, filepath) -> Dict[str, Set[str]]:
        filepath = str(filepath)
        keywords = {}

        if filepath.lower().endswith('.doc'):
            filepath = convert_doc_to_docx(filepath)

        if filepath.lower().endswith('.docx'):
            filepath = convert_docx_to_pdf(filepath)
            # return keywords
            # doc: Document = read_docx(filepath)
            # tables = doc.tables
            #
            # for table in tables:
            #     for marker in self.markers:
            #         # if idx := contains_marker(table.rows, marker):
            #         #     keywords.update(table.row_cells(idx))
            #
            #         columns = table_to_columns(table)
            #         for column in columns:
            #             if contains_marker(column, marker):
            #                 keywords.update(column)
            #
            # return keywords.difference(self.markers).difference({''})

        if filepath.lower().endswith('.pdf'):
            try:
                tables = camelot.read_pdf(filepath, pages='all')

            except Exception:
                pdf = Pdf.open(filepath, allow_overwriting_input=True)
                pdf.remove_unreferenced_resources()
                pdf.save()
                pdf.close()

                tables = camelot.read_pdf(filepath, pages='all')

            for table in tables:
                df = table.df
                df.columns = df.iloc[0]
                df.drop(0, axis=0, inplace=True)

                for marker in self.markers:
                    if (idx := index_of_marker(df.columns, marker)) != -1:
                        keywords[marker] = set(df.iloc[:, idx])

            return keywords

        raise Exception('Unable to parse file: ' + filepath)


def files(docs_path=None) -> Iterator[PathLike]:
    docs_path = docs_path or DATA_PATH.joinpath('documents')
    return map(docs_path.joinpath, list_files(docs_path))


def all_to_docx():
    for file in progressbar(list(map(str, files())), ncols=100):
        if file.lower().endswith('.pdf'):
            convert_pdf_to_docx(file, True)
        if file.lower().endswith('doc'):
            convert_doc_to_docx(file, True)


if __name__ == '__main__':
    extractor = Extractor(MARKERS)
    # extractor.extract()
    # f = DATA_PATH.joinpath('documents', '(236863) Создание и развитие студенческого клуба.pdf') # good

    # f = DATA_PATH.joinpath('documents', '(243940) 27_Алгоритмы_и_структуры_данных_ОГНП_КТ.pdf')
    # f = DATA_PATH.joinpath('documents', '(241976) Б1_28_1.2_Мультимедиа_технологии_ОГНП_КТ.pdf')

    df = pd.DataFrame({i: [] for i in ('FILE_NAME',) + MARKERS})

    for file in progressbar(list(files())[:100], ncols=100):
        try:
            file_keywords = extractor.extract(file)

            for marker, keywords in file_keywords.items():
                keywords = set(map(clean_keyword, list(keywords)))
                keywords = reduce(set.__or__, map(split, keywords))
                file_keywords[marker] = ','.join(keywords)

            df = pd.concat((df, pd.DataFrame({'FILE_NAME': [file.name], **{k: [v] for k, v in file_keywords.items()}})))

            # keywords_[file.name] = ','.join(file_keywords)

        except Exception as e:
            print('Error:', file, e)
            continue

    # print(keywords)

    # print(indexes_of('hello. ind.s me. I', '.'))



    #
    p = DATA_PATH.joinpath('results')
    df.to_csv(str(p.joinpath('tables.small.v3.3.csv')))
    # p.mkdir(exist_ok=True)
    # with open(str(p.joinpath('tables.small.v1.csv')), 'w', encoding='utf-8') as f:
    #     for k, v in keywords.items():
    #         f.write(k + '|' + ','.join(v) + '\n')

    # print(keywords)

    # pd.DataFrame({
    #     'FILE_NAME': keywords_.keys(),
    #     'KEYWORDS': keywords_.values()
    # }).to_csv(
    #     str(p.joinpath('tables.small.v3.2.csv'))
    # )

    # tables = camelot.read_pdf('D:\\projects\\rpd-keyword-extraction\\data\\documents\\(206832) 58 Разработка распределенных приложении.pdf')

    # print(list(map(process, extractor.extract('D:\\projects\\rpd-keyword-extraction\\data\\documents\\(223806) 450304 Б1.54 Рекомендательные системы.pdf'))))

    # print(fix_column(tables[1].iloc[:, -1]))

    # print(list(map(process, extractor.extract(
    #     'D:\\projects\\rpd-keyword-extraction\\data\\documents\\(206832) 58 Разработка распределенных приложении.pdf'
    # ))))
