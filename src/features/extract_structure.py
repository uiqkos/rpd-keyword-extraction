import logging
import os
os.environ['LD_LIBRARY_PATH'] = 'C:\\Program Files\\gs\\gs9.55.0\\bin\\gsdll64.dll'
logging.disable()

from itertools import filterfalse
from dataclasses import dataclass
from os import PathLike
from typing import List, Iterator, Set

import camelot
import pandas as pd
from tqdm import tqdm as progressbar

from src.features.utils import convert_doc_to_docx, process, convert_pdf_to_docx, index_of_marker, convert_docx_to_pdf
from src.settings import DATA_PATH, MARKERS
from src.utils import list_files


@dataclass
class Extractor:
    markers: List[str]

    def extract(self, filepath) -> Set[str]:
        filepath = str(filepath)
        keywords = set()

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
            tables = camelot.read_pdf(filepath, pages='all')

            for table in tables:
                df = table.df
                df.columns = df.iloc[0]
                df.drop(0, axis=0, inplace=True)

                for marker in self.markers:
                    if (idx := index_of_marker(df.columns, marker)) != -1:
                        keywords.update(df.iloc[:, idx])

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

    keywords = {}

    for file in progressbar(list(files())[:100], ncols=100):
        try:
            keywords[file.name] = ','.join(list(filterfalse(''.__eq__, map(process, extractor.extract(file)))))

        except Exception as e:
            print('Error:', file, e)
            continue

    p = DATA_PATH.joinpath('results')
    p.mkdir(exist_ok=True)
    # with open(str(p.joinpath('tables.small.v1.csv')), 'w', encoding='utf-8') as f:
    #     for k, v in keywords.items():
    #         f.write(k + '|' + ','.join(v) + '\n')

    # print(keywords)

    pd.DataFrame({
        'FILE_NAME': keywords.keys(),
        'KEYWORDS': keywords.values()
    }).to_csv(
        str(p.joinpath('tables.small.v2.2.csv'))
    )

    # tables = camelot.read_pdf('D:\\projects\\rpd-keyword-extraction\\data\\documents\\(206832) 58 Разработка распределенных приложении.pdf')

    # print(list(map(process, extractor.extract('D:\\projects\\rpd-keyword-extraction\\data\\documents\\(223806) 450304 Б1.54 Рекомендательные системы.pdf'))))

    # print(fix_column(tables[1].iloc[:, -1]))

    # print(list(map(process, extractor.extract(
    #     'D:\\projects\\rpd-keyword-extraction\\data\\documents\\(206832) 58 Разработка распределенных приложении.pdf'
    # ))))
