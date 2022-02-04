import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from src.extract_structure import files
from src.settings import DATA_PATH
from src.stages import *


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

    keywords = ExtractKeywords(MARKERS).apply((fs := list(files(DATA_PATH / 'tables'))), [None] * len(fs))

    df = pd.DataFrame(keywords)
    df['FILE_NAME'] = list(map(attrgetter('name'), fs))
    df.set_index('FILE_NAME', drop=True, inplace=True)
    df.to_csv(DATA_PATH / 'results' / 'tables.full.v4.1.csv')

    # ExtractTables(save_path=tables_path, generator=False, overwrite=False).apply_threading(list(files()))
