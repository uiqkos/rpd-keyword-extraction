from typing import Callable, Iterable

from more_itertools import flatten
from sklearn.feature_extraction.text import CountVectorizer

from src.utils import identity


# todo: сделать кэширование векторов

class GroupMetric:
    def __init__(self,
                 single_metric: Callable[[..., ...], float],
                 group_metric: Callable[[Iterable[float]], float]):

        self.keyword_metric = single_metric
        self.group_metric = group_metric

    def __call__(self, kwg1, kwg2):
        return self.group_metric(list(map(
            self.keyword_metric,
            flatten([kw] * len(kwg2) for kw in kwg1),  # kw1, kw2, ..., kw1, kw2, ..., kw1, kw2, ...
            flatten([kwg2] * len(kwg1))  # kw1, kw1, kw1, ..., kw2, kw2, kw2, ...
        )))


class ComparatorFromDistanceMetric:
    def __init__(self, metric, threshold, max=1.):
        self.metric = metric
        self.threshold = threshold
        self.max = max

    def __call__(self, *args, **kwargs):
        return (self.max - self.metric(*args, **kwargs)) > self.threshold


class BagOfWordsDistance:
    def __init__(
        self,
        distance_metric: Callable,
        preprocessor: Callable[[str], str] = None,
        vectorizer_kwargs: dict = None
    ):
        preprocessor = preprocessor or identity
        vectorizer_kwargs = vectorizer_kwargs or {}

        self._vectorizer = CountVectorizer(
            token_pattern=r'\w+',
            preprocessor=preprocessor,
            **vectorizer_kwargs
        )

        self.distance_metric = distance_metric

    def __call__(self, kw1, kw2):
        kw1, kw2 = self._vectorizer.fit_transform([kw1, kw2]).toarray()
        # if not any(kw1) or not any(kw2):  # all zeroes
        #     return 0.

        return self.distance_metric(kw1, kw2)
