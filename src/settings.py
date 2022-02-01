import pathlib

ROOT_PATH = pathlib.Path(__file__).parent.parent.absolute()
SRC_PATH = pathlib.Path(__file__).parent.absolute()
DATA_PATH = ROOT_PATH.joinpath('data')


MARKERS = (
    'Планируемые результаты обучения',
    'Наименование раздела дисциплины',
    'Наименование раздела дисциплины (модуля)',
    'Содержание',

    # ГИА
    'Наименование оценочного средства',

)
