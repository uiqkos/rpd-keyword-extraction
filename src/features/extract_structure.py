import os

import camelot

os.environ['LD_LIBRARY_PATH'] = 'C:\\Program Files\\gs\\gs9.55.0\\bin\\gsdll64.dll'

from dataclasses import dataclass
from os import PathLike
from pprint import pprint
from typing import List, Iterator, Set

import pandas as pd
# import camelot
import tabula
from docx import Document as read_docx
from docx.document import Document

from src.features.utils import convert_doc_to_docx, contains_marker, process, fix_column
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
            tables = tabula.read_pdf(filepath, pages='all')

            for table in tables:
                # df: pd.DataFrame = table.df
                df = table

                for marker in self.markers:
                    # rows
                    # if idx := contains_marker(df.axes[0], marker):
                    #     keywords.update(df.iloc[idx, :])

                    for column_name in df:
                        column = fix_column(df[column_name])
                        if contains_marker(column, marker) or contains_marker([column], marker):
                            keywords.update(column)

            return keywords.difference(self.markers)

        if filepath.lower().endswith('.doc'):
            filepath = convert_doc_to_docx(filepath)

        if filepath.lower().endswith('.docx'):
            doc: Document = read_docx(filepath)
            tables = doc.tables

            for table in tables:
                for marker in self.markers:
                    if idx := contains_marker(table.rows, marker):
                        keywords.update(table.row_cells(idx))

                    if idx := contains_marker(table.columns, marker):
                        keywords.update(table.column_cells(idx))

            return keywords.difference(self.markers)

        raise Exception('Unable to parse file: ' + filepath)


def files(docs_path=None) -> Iterator[PathLike]:
    docs_path = docs_path or DATA_PATH.joinpath('documents')
    return map(docs_path.joinpath, list_files(docs_path))


if __name__ == '__main__':
    # extractor = Extractor(MARKERS)

    tables = camelot.read_pdf('D:\\projects\\rpd-keyword-extraction\\data\\documents\\(206832) 58 Разработка распределенных приложении.pdf')

    # print(extractor.extract())

    # print(fix_column(tables[1].iloc[:, -1]))

    # print(list(map(process, extractor.extract(
    #     'D:\\projects\\rpd-keyword-extraction\\data\\documents\\(206832) 58 Разработка распределенных приложении.pdf'
    # ))))
