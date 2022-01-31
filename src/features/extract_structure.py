import logging
import os

import camelot
import pdf2docx

os.environ['LD_LIBRARY_PATH'] = 'C:\\Program Files\\gs\\gs9.55.0\\bin\\gsdll64.dll'
logging.disable()

from dataclasses import dataclass
from os import PathLike
from pprint import pprint
from typing import List, Iterator, Set

import pandas as pd
# import camelot
import tabula
from tqdm import tqdm as progressbar
from docx import Document as read_docx
from docx.document import Document

from src.features.utils import convert_doc_to_docx, contains_marker, process, fix_column, table_to_columns, \
    convert_pdf_to_docx
from src.settings import DATA_PATH, MARKERS
from src.utils import list_files


@dataclass
class Extractor:
    markers: List[str]

    def extract(self, filepath) -> Set[str]:
        filepath = str(filepath)
        keywords = set()

        if filepath.lower().endswith('.pdf'):
            # tables = camelot.read_pdf(filepath, pages='all')
            # tables = tabula.read_pdf(filepath, pages='all')
            #
            # for table in tables:
            #     # df: pd.DataFrame = table.df
            #     df = table
            #
            #     for marker in self.markers:
            #         # rows
            #         # if idx := contains_marker(df.axes[0], marker):
            #         #     keywords.update(df.iloc[idx, :])
            #
            #         for column_name in df:
            #             column = fix_column(df[column_name])
            #             if contains_marker(column, marker) or contains_marker([column], marker):
            #                 keywords.update(column)
            #
            # return keywords.difference(self.markers)
            filepath = convert_pdf_to_docx(filepath)

        if filepath.lower().endswith('.doc'):
            filepath = convert_doc_to_docx(filepath)

        if filepath.lower().endswith('.docx'):
            doc: Document = read_docx(filepath)
            tables = doc.tables

            for table in tables:
                for marker in self.markers:
                    # if idx := contains_marker(table.rows, marker):
                    #     keywords.update(table.row_cells(idx))

                    columns = table_to_columns(table)
                    for column in columns:
                        if contains_marker(column, marker):
                            keywords.update(column)

            return keywords.difference(self.markers)

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
    # all_to_docx()
    extractor = Extractor(MARKERS)

    keywords = {}

    for file in progressbar(list(files())[:1000], ncols=100):
        try:
            if not str(file).endswith('.docx'):
                continue
            keywords[file.name] = list(map(process, extractor.extract(file)))

        except:
            continue

    p = DATA_PATH.joinpath('results')
    p.mkdir(exist_ok=True)
    with open(str(p.joinpath('tables.small.v1.csv')), 'w', encoding='utf-8') as f:
        for k, v in keywords.items():
            f.write(','.join([k, *v]) + '\n')

    # pd.DataFrame(keywords).to_csv()

    # tables = camelot.read_pdf('D:\\projects\\rpd-keyword-extraction\\data\\documents\\(206832) 58 Разработка распределенных приложении.pdf')

    # print(list(map(process, extractor.extract('D:\\projects\\rpd-keyword-extraction\\data\\documents\\(206832) 58 Разработка распределенных приложении.docx'))))

    # print(fix_column(tables[1].iloc[:, -1]))

    # print(list(map(process, extractor.extract(
    #     'D:\\projects\\rpd-keyword-extraction\\data\\documents\\(206832) 58 Разработка распределенных приложении.pdf'
    # ))))
