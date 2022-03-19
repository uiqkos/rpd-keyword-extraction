import json
from functools import reduce
from itertools import filterfalse, count
from statistics import mean
from typing import Callable, Iterable

import numpy as np
from more_itertools import ilen
from scipy.spatial.distance import cosine
from sklearn.feature_extraction.text import CountVectorizer

from src.clustering.bagofwords import Pool
from src.clustering.metrics import GroupMetric, ComparatorFromDistanceMetric, BagOfWordsDistance
from src.settings import DATA_PATH
from src.stages.stage import Stage
from src.utils import compose


class VecGrouper(Stage):
    def __init__(self,
                 threshold: float,
                 preprocessor: Callable[[str], str],
                 ngram_range=None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.threshold = threshold
        self.pool = Pool(
            ComparatorFromDistanceMetric(
                metric=GroupMetric(
                    BagOfWordsDistance(
                        cosine, preprocessor, dict(ngram_range=ngram_range or (1, 1))
                    ),
                    np.mean
                ),
                threshold=threshold
            )
        )

    def _save_groups(self, groups, pc):
        if self.verbose:
            print(self.save_path.name)

        with open(self.save_path, 'w', encoding='utf-8') as file:
            json.dump(
                {
                    'clusters': groups
                },
                file,
                ensure_ascii=False,
                indent=4,
            )

    def apply(self, docs: Iterable[Iterable[str]]):
        docs = reduce(set.__or__, map(set, docs))
        docs.remove('')

        groups = self.pool.reduce(docs, continue_if_merge=True)

        if self.save:
            pc = round((ilen(filterfalse(compose(len, (1).__eq__), groups)) / len(groups)), 2)
            self._save_groups(groups, pc)

        return groups
