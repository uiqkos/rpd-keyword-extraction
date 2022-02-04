import json
from itertools import filterfalse
from multiprocessing.pool import ThreadPool

import numpy as np
import os
import re
import time
from abc import ABC, abstractmethod
from functools import partial, reduce
from operator import attrgetter
from pathlib import Path
from typing import Iterator, List, Tuple, Union
from urllib import request

import camelot
import pandas as pd
from tqdm import tqdm
from openpyxl.pivot.fields import TupleList
from pikepdf import Pdf

from src.utils import convert_doc_to_docx, convert_docx_to_pdf, index_of_marker


progressbar = partial(tqdm, ncols=100)


class Stage(ABC):
    def __init__(
        self,
        generator=False,
        save=False,
        save_path: Path = None,
        unpack_result=False,
        errors: str = 'ignore'
    ):
        self.generator = generator
        self.save = save
        self.save_path = save_path
        self.unpack_result = unpack_result
        self.errors = errors

    @abstractmethod
    def apply(self, *args, **kwargs):
        pass

    @abstractmethod
    def apply_generator(self, *args, **kwargs):
        pass


class Load(Stage):
    def __init__(
            self,
            file_ids,
            file_names,
            links,
            ignore_exist=False,
            sleep: int = 1,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.file_ids = file_ids
        self.file_names = file_names
        self.links = links
        self.sleep = sleep

        if ignore_exist:
            file_names = list(zip(*os.walk(self.save_path)))[2][0]
            id_pattern = re.compile(r'^\((\d+)\)')
            self.ignore_ids = {int(re.findall(id_pattern, file_name)[0]) for file_name in file_names}
        else:
            self.ignore_ids = set()

    def apply(self) -> List[Path]:
        return list(self.apply_generator())

    def apply_generator(self) -> Iterator[Path]:
        for file_id, file_name, link in progressbar(zip(self.file_ids, self.file_names, self.links)):
            if file_id in self.ignore_ids:
                continue

            file_name = re.sub(r'[^\w\-_\. ]', '', file_name)
            file_name = f"({file_id}) {file_name}"
            file_path = self.save_path.joinpath(file_name)
            _, msg = request.urlretrieve(link, file_path)

            yield file_path

            time.sleep(self.sleep)


class ConvertToPdf(Stage):
    def __init__(self, overwrite=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.overwrite = overwrite

    def apply(self, file_paths) -> List[Path]:
        return list(self.apply_generator(file_paths))

    def apply_generator(self, file_paths) -> Iterator[Path]:
        for file_path in progressbar(file_paths):
            if file_path.name.endswith('.doc'):
                file_path = convert_doc_to_docx(file_path, self.overwrite)

            if file_path.name.endswith('.docx'):
                file_path = convert_docx_to_pdf(file_path, self.overwrite)

            if file_path.name.lower().endswith('.pdf'):
                yield file_path

            raise Exception('Unable to parse file: ' + file_path)


class ExtractTables(Stage):
    def __init__(self, save_path, fix_pdf=True, overwrite=True, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fix_pdf = fix_pdf
        self.save_path = save_path
        self.save = bool(save_path)
        self.overwrite = overwrite

    def _extract_tables(self, file_path) -> List[pd.DataFrame]:
        try:
            tables = camelot.read_pdf(str(file_path), pages='all')

        except Exception:
            pdf = Pdf.open(file_path, allow_overwriting_input=True)
            pdf.remove_unreferenced_resources()
            pdf.save()
            pdf.close()

            tables = camelot.read_pdf(str(file_path), pages='all')

        res = []

        for table in tables:
            df: pd.DataFrame = table.df
            df.columns = df.iloc[0]
            df.drop(0, axis=0, inplace=True)
            df = df.applymap(str)
            res.append(df)

        return res

    def _save_tables(self, file_path, tables, overwrite=True):
        with open(file_path, 'w', encoding='utf-8') as f:

            json.dump({
                'tables': list(map(partial(
                    pd.DataFrame.to_dict, orient='split'
                ), tables))
            }, f, ensure_ascii=False)

    def _process_file_path(self, file_path):
        new_file_path = None

        if self.save:
            new_file_path = self.save_path.joinpath(file_path.name + '.tables.json')
            if new_file_path.is_file() and not self.overwrite:
                return

        try:
            tables = self._extract_tables(file_path)

        except Exception as e:
            if self.errors == 'ignore':
                return
            raise e

        if new_file_path:
            self._save_tables(new_file_path, tables)

        return new_file_path, tables

    def apply(self, file_paths) -> List[Union[Tuple[Path, List[pd.DataFrame]], List[pd.DataFrame]]]:
        return list(self.apply_generator(file_paths))

    def apply_generator(self, file_paths) -> Iterator[Tuple[Path, List[pd.DataFrame]]]:
        for file_path in progressbar(file_paths):
            if res := self._process_file_path(file_path):
                yield res

    def apply_threading(self, file_paths, workers=4):
        pool = ThreadPool(workers)
        return pool.map(self._process_file_path, progressbar(file_paths))


class ExtractKeywords(Stage):

    def __init__(self, markers, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.markers = markers

    @staticmethod
    def _clean(word):
        word = str(word)
        word = re.sub(r'\n', '', word)
        word = re.sub(r'\w+ (\d\. ?)+', '', word)
        word = re.sub(r'\(.*\)', '', word)
        word = re.sub(r' ?[-–●•] ', '', word)
        word = re.sub(r'-', '', word)
        word = re.sub(r'\w+:', '', word)
        word = re.sub(r' +', ' ', word)
        word = re.sub(r'\.', '', word)
        word = re.sub(r'\d+', ',', word)
        word = word.strip()

        return word

    @staticmethod
    def _split(word):
        seqs = set()
        buffer = []

        def release_buffer():
            if buffer:
                seqs.add(''.join(buffer))
                buffer.clear()

        for c in word:
            if c in ('.', ',', ';'):
                release_buffer()
            elif buffer or c != ' ':
                buffer.append(c)

        release_buffer()

        return seqs

    def apply(self, file_paths, files_tables):
        return list(self.apply_generator(file_paths, files_tables))

    def apply_generator(self, file_paths, files_tables):
        for file_path, tables in progressbar(zip(file_paths, files_tables)):
            if not tables:
                json_tables = json.load(open(file_path, 'r', encoding='utf-8'))['tables']
                tables = map(partial(pd.read_json, orient='split'), map(json.dumps, json_tables))

            keywords = {}
            for table in tables:
                for marker in self.markers:
                    if (idx := index_of_marker(table.columns, marker)) != -1:
                        kw = set(table.iloc[:, idx])
                        kw = map(self._clean, kw)
                        kw = filterfalse(''.__eq__, kw)
                        kw = map(self._split, kw)
                        kw = reduce(set.__or__, kw, set())
                        keywords[marker] = ','.join(kw)

            yield keywords


class Pipeline:
    def __init__(self, stages):
        self.stages = stages

    def apply(self, *args):
        unpack = True
        for stage in self.stages:
            if not unpack:
                args = (args,)
            if stage.generator:
                args = stage.apply_generator(*args)
            else:
                args = stage.apply(*args)

            unpack = stage.unpack_result

        return args
