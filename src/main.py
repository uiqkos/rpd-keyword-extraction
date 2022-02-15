import warnings
from functools import reduce, partial
from operator import attrgetter
from pprint import pprint

import pandas as pd

from src.PoSTagKeywordFilter import PoSTagKeywordFilter
from src.extract_structure import files
from src.morphy_utils import encode_masks
from src.stages import Pipeline, ExtractKeywords

warnings.simplefilter(action='ignore', category=FutureWarning)

from src.settings import DATA_PATH

MARKERS = (
    'Планируемые результаты обучения',
    'Наименование раздела дисциплины',
    'Наименование раздела дисциплины (модуля)',
    'Содержание',

    # ГИА
    'Наименование оценочного средства',
)


if __name__ == '__main__':
    tables_path = DATA_PATH.joinpath('tables')

    # pipeline = Pipeline((
    #     ExtractTables(save_path=tables_path, generator=False, overwrite=False),
    # ))
    #
    # pipeline.apply(list(files()))

    pipeline = Pipeline((
        ExtractKeywords(MARKERS, flatten_results=True, seps=(';', '.')),
        PoSTagKeywordFilter(masks=encode_masks(
            # ('прил', 'сущ'),
            ('сущ', 'сущ', 'сущ'),
            ('сущ', 'сущ', 'прил', 'сущ'),
            ('нар', 'глаг', 'сущ'),
            # ('сущ', 'глаг'),
            # ('мест', 'глаг'),
        ), str_result=True)
    ))

    keywords = pipeline.apply((fs := list(files(DATA_PATH / 'tables'))[:200]))

    df = pd.DataFrame.from_records(
        data=zip(map(attrgetter('name'), fs), keywords),
        columns=['filename', 'keywords']
    )
    # df['FILE_NAME'] = list(map(attrgetter('name'), fs))
    df.set_index('filename', drop=True, inplace=True)
    df.to_csv(DATA_PATH / 'results' / 'pos.small.v1.1.csv')
