import json
import re
from functools import partial, reduce
from itertools import zip_longest, filterfalse

import pandas as pd

from src.stages.stage import Stage
from src.utils.utils import progressbar, index_of_marker


class ExtractKeywords(Stage):
    def __init__(self, markers, flatten_results=False, seps=('.', ',', ';'), *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.markers = markers
        self.flatten_results = flatten_results
        self.seps = seps

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

    def apply(self, file_path, tables=None):
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

        if self.flatten_results:
            for value in keywords.values():
                return value.split(',')
        else:
            return keywords
