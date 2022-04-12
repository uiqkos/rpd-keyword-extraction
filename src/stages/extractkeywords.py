import json
import re
from functools import partial, reduce
from itertools import filterfalse
from operator import indexOf
from pathlib import Path
from typing import Iterable, Union, Dict, List

import pandas as pd

from src.stages.stage import Stage


class ExtractKeywords(Stage):
    def __init__(
        self,
        markers: Iterable[str],
        flatten_results: bool = False,
        seps: Iterable[str] = ('.', ',', ';'),
        *args, **kwargs
    ):
        """
        Стадия извлекает первичные ключевые слова (последовательности слов, не разделенные знаками препинания)

        Parameters
        ----------
        markers: Iterable[str]
            названия колонок в таблицах, из которых извлекать ключевые слова
        flatten_results: bool
            Распаковка результата: преобразование Dict[str, str] в List[str]
        seps: Iterable[str]
            Пунктуация, по которой разделяются слова
        """
        super().__init__(*args, **kwargs)

        self.markers = markers
        self.flatten_results = flatten_results
        self.seps = seps

    @staticmethod
    def _process(s):
        return ' '.join(re.findall(r'\w+', str(s).lower()))

    @staticmethod
    def _index_of_marker(container, marker) -> int:
        marker = ExtractKeywords._process(marker)

        def match(s):
            return ExtractKeywords._process(s) == marker

        try:
            idx = indexOf(list(map(match, container)), True)

        except ValueError:
            idx = -1

        return idx

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
        word = re.sub(r'', '', word)
        word = re.sub(r'\d+', ',', word)
        word = word.strip()

        return word

    def _split(self, word):
        seqs = set()
        buffer = []

        def release_buffer():
            if buffer:
                seqs.add(''.join(buffer))
                buffer.clear()

        for c in word:
            if c in self.seps:
                release_buffer()
            elif buffer or c != ' ':
                buffer.append(c)

        release_buffer()

        return seqs

    def apply(
        self,
        file_path: Union[Path, str] = None,
        tables: Iterable[pd.DataFrame] = None
    ) -> Union[Dict[str, str], List[str]]:
        """
        Извлекает первичные ключевые слова из таблиц

        Parameters
        ----------
        file_path: Path | str
            путь до json файла с таблицами
        tables: Iterable[pd.DataFrame]
            Таблицы

        Returns
        -------
            Словарь {колонка: ключевые слова} или список ключевых слов (flatten_results)
        """
        if not tables:
            json_tables = json.load(open(file_path, 'r', encoding='utf-8'))['tables']
            tables = map(partial(pd.read_json, orient='split'), map(json.dumps, json_tables))

        keywords = {}
        for table in tables:
            for marker in self.markers:
                if (idx := self._index_of_marker(table.columns, marker)) != -1:
                    kw = set(table.iloc[:, idx])
                    kw = map(self._clean, kw)
                    kw = filterfalse(''.__eq__, kw)
                    kw = map(self._split, kw)
                    kw = reduce(set.__or__, kw, set())
                    keywords[marker] = ','.join(kw)

        if self.flatten_results:
            for value in keywords.values():
                return value.split(',')
        else:
            return keywords
