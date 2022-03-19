from functools import reduce, partial
from os import PathLike
from typing import List, Union, Iterable

import pandas as pd

from src.settings import DATA_PATH
from src.utils.utils import file_names, file_paths


def merge(
    paths: Iterable[Union[PathLike, str]],
    read_kwargs=None,
    concat_kwargs=None,
    columns_take=None
) -> pd.DataFrame:
    read_kwargs = read_kwargs or {}
    concat_kwargs = concat_kwargs or {}

    concat = partial(pd.concat, **concat_kwargs)
    read = partial(pd.read_excel, **read_kwargs)

    df = concat(map(read, paths))

    if columns_take is not None:
        df.drop(df.columns[columns_take:], axis=1, inplace=True)

    return df


if __name__ == '__main__':
    path = DATA_PATH / 'raw' / 'data_validation'
    paths = list(filter(
        lambda p: '22.xlsx' not in p.name,
        file_paths(DATA_PATH / 'raw' / 'data_validation')
    ))

    df = merge(paths, columns_take=3)

    print(df.head(10))
    print(df.shape)
    print(df.columns)

    df.to_csv(DATA_PATH / 'raw' / 'val_full.v1.csv', index=False)

