from abc import ABC, abstractmethod
from collections import Counter
from functools import reduce, partial
from typing import List, Callable

import numpy as np
from more_itertools import minmax

from src.stages.cluster.embeddings.tokenizer import Tokenizer


class Vectorizer(ABC):
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def fit(self, keywords):
        pass

    @abstractmethod
    def apply(self, keyword: str):
        pass

    def __call__(self, *args, **kwargs):
        return self.apply(*args, **kwargs)


class ReduceVectorizer(Vectorizer):
    def __init__(self, tokenizer, fn: Callable = None):
        super(ReduceVectorizer, self).__init__(tokenizer)

        self.fn = fn or partial(np.mean, axis=0)

    def apply(self, keyword: str):
        indexes = self.tokenizer.tokenize(keyword)
        embeddings = self.tokenizer.vectorize(indexes, to=np.array)

        return self.fn(embeddings)


class FrequencyVectorizer(Vectorizer):
    def __init__(self, tokenizer: Tokenizer, *args, **kwargs):
        super(FrequencyVectorizer, self).__init__(tokenizer)

        self.word_counter = Counter()
        self.mn = 0
        self.mx = 0

    def fit(self, keywords: List[List[str]]):
        all_keywords = set(reduce(list.__add__, keywords))
        all_keywords.difference_update({'', ' '})

        self.word_counter = Counter(
            reduce(
                list.__add__,
                map(self.tokenizer.tokenize, all_keywords)
            )
        )

        self.mn, self.mx = minmax(self.word_counter.values())

    def normalize(self, x):
        return np.array([(x_ - self.mn) / ((self.mx - self.mn) or 1) for x_ in x])

    def apply(self, keyword: str):
        indexes = self.tokenizer.tokenize(keyword)
        counts = list(map(self.word_counter.get, indexes))  # n x 1
        vec = 1 - self.normalize(counts)
        embeddings = self.tokenizer.vectorize(indexes, to=np.array)  # n x 300

        return embeddings.T @ vec  # 300 x 1
