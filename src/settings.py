import pathlib

ROOT_PATH = pathlib.Path(__file__).parent.parent.absolute()
SRC_PATH = pathlib.Path(__file__).parent.absolute()
DATA_PATH = ROOT_PATH.joinpath('data')
MODELS_PATH = ROOT_PATH.joinpath('models')

