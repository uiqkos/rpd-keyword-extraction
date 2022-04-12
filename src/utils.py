import os
from functools import reduce, partial
from functools import wraps
from os import PathLike
from pathlib import Path
from typing import Iterator
from typing import Union, Iterable

import pandas as pd
from tqdm import tqdm

tqdm = partial(tqdm, ncols=100)


def file_names(path):
    return list(zip(*os.walk(path)))[2][0]


def file_paths(path) -> Iterator[Path]:
    return map(path.joinpath, file_names(path))


def identity(o):
    return o


def compose2(f1, f2):
    return lambda *args, **kwargs: f2(f1(*args, **kwargs))


def compose(*fs):
    return reduce(compose2, fs)


def and_2predicates(p1, p2):
    return lambda *args, **kwargs: p1(*args, **kwargs) and p2(*args, **kwargs)


def and_predicates(*ps):
    return reduce(and_2predicates, ps)


def tupled(f, input=True, output=False):
    @wraps(f)
    def wrapper(tup):
        if input:
            result = f(*tup)
        else:
            result = f(tup)

        if output:
            if not isinstance(result, tuple):
                return result,

        return result

    return wrapper


def expand_dict(dct: dict, seq_type=tuple):
    new = {}
    for key, value in dct.items():
        if isinstance(key, seq_type):
            for key_ in key:
                new[key_] = value

        else:
            new[key] = value

    return new


def merge_csv(
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


def keywords_from_dataframe(df: Union[pd.Series, pd.DataFrame]):
    return (
        df
            .dropna()
            .map(lambda s: list(map(str.strip, s.split(','))))
            .tolist()
    )
