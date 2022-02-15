from functools import partial
from more_itertools import flatten
from operator import attrgetter
from typing import List, Callable, Iterable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.metrics.distance import edit_distance, jaro_similarity

from src.clustering.keyword import Keyword, KeywordGroup
from src.utils import identity, compose


class KeywordGroupMetric:
    def __init__(self,
                 keyword_metric: Callable[[Keyword, Keyword], float],
                 group_metric: Callable[[Iterable[float]], float]):

        self.keyword_metric = keyword_metric
        self.group_metric = group_metric

    def __call__(self, kwg1: KeywordGroup, kwg2: KeywordGroup):
        return self.group_metric(list(map(
            self.keyword_metric,
            flatten([kw] * len(kwg2.keywords) for kw in kwg1.keywords),  # kw1, kw2, ..., kw1, kw2, ..., kw1, kw2, ...
            flatten([kwg2.keywords] * len(kwg1.keywords))  # kw1, kw1, kw1, ..., kw2, kw2, kw2, ...
        )))


def normal_form_equals(kw1: Keyword, kw2: Keyword):
    return float(kw1.stemmed == kw2.stemmed)


class FromStringMetric:
    def __init__(self,
                 string_metric: Callable[[str, str, ...], float],
                 kw_to_str: Callable[[Keyword], str] = None,
                 # distance_to_similarity: Callable[[float, str, str], float] = None,
                 **kwargs):
        self.string_metric = partial(string_metric, **kwargs)
        self.kw_to_str = kw_to_str or identity

    def __call__(self, kw1: Keyword, kw2: Keyword):
        return self.string_metric(self.kw_to_str(kw1), self.kw_to_str(kw2))


_keyword_to_string_stemmed = compose(attrgetter('stemmed'), ' '.join)

edit_similarity = FromStringMetric(
    string_metric=lambda s1, s2: 1 - (edit_distance(s1, s2) / max(len(s1), len(s2))),
    kw_to_str=_keyword_to_string_stemmed
)

edit_similarity_transpositions = FromStringMetric(
    string_metric=lambda s1, s2: 1 - (edit_distance(s1, s2, transpositions=True) / max(len(s1), len(s2))),
    kw_to_str=_keyword_to_string_stemmed
)

jaro_similarity_metric = FromStringMetric(
    string_metric=jaro_similarity,
    kw_to_str=_keyword_to_string_stemmed
)


class TfIdf:
    def __init__(self, docs: List[List[Keyword]], distance_metric: Callable = None):
        self._vectorizer = TfidfVectorizer()
        self._vectorizer.fit(
            ','.join(' '.join(kw.stemmed) for kw in doc)
            for doc in docs
        )
        self.distance_metric = distance_metric or np.array_equal

    def __call__(self, kw1: Keyword, kw2: Keyword) -> float:
        v1 = self._vectorizer.fit_transform([
            ' '.join(word for word in kw1.stemmed)
        ]).tocoo().data
        v2 = self._vectorizer.fit_transform([
            ' '.join(word for word in kw2.stemmed)
        ]).tocoo().data
        return self.distance_metric(v1, v2)
