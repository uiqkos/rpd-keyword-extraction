from collections import Counter
from copy import copy
from dataclasses import dataclass
from functools import reduce, partial
from itertools import filterfalse
from operator import attrgetter, itemgetter
from typing import List, Iterable, Callable, Tuple, Set

from src.token import Token


class Doc:
    def __init__(self, words: Iterable[str]):
        # self.ignore = ignore or set()
        #
        # self.tokens = list(filter(
        #     lambda t: t.text not in self.ignore,
        #     map(partial(Token, **kwargs), words)
        # ))
        # self.tokens = list(map(Token, words))
        # self.counter = Counter(words)
        self.tokens = []
        self.counter = Counter()

        for word in words:
            token = Token(word)
            self.counter[token.normal_form] += 1
            self.tokens.append(token)

    def count(self, word):
        return self.counter[word]

    def frequency(self, word):
        return self.count(word) / sum(self.counter.values())

    def best_seq(
        self,
        word_metric: Callable[['Doc', str], float],
        seq_metric: Callable[[List[float]], float],
        upper_threshold: float,
        lower_threshold: float,
        max_count: int = 3,
        min_count: int = 1
    ):
        all_seqs = reduce(
            set.__or__, map(partial(
                self._best_seq,
                word_metric=word_metric,
                seq_metric=seq_metric,
                upper_threshold=upper_threshold,
                lower_threshold=lower_threshold,
                max_count=max_count,
                min_count=min_count
            ), range(len(self.tokens)))
        )

        sorted_seqs = sorted(all_seqs, key=itemgetter(1), reverse=True)

        return [
            ' '.join(map(attrgetter('text'), seq[0])) + ' -> ' + str(seq[1])
            for seq in sorted_seqs
        ]

    def _best_seq(
            self,
            start: int,
            word_metric: Callable[['Doc', str], float],
            seq_metric: Callable[[Iterable[float]], float],
            upper_threshold: float,
            lower_threshold: float,
            max_count: int = 3,
            min_count: int = 1
    ) -> Set[Tuple[Tuple[Token, ...], float]]:
        seqs = set()
        seq = []
        metrics = []

        if start >= len(self.tokens):
            return seqs

        for i in range(start, min(len(self.tokens), start + max_count)):
            token = self.tokens[i]
            seq.append(token)

            metrics.append(word_metric(self, token.normal_form))

            if (seq_metric_value := seq_metric(metrics)) < lower_threshold or seq_metric_value > upper_threshold \
                    or (len(metrics) > 1 and seq_metric_value < seq_metric(metrics[:-1])):
                break

            if len(seq) >= min_count:
                seqs.add((tuple(seq), seq_metric_value))

        return seqs
