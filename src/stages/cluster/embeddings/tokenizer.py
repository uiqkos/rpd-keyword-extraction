from functools import partial
from typing import Callable

import gensim
import nltk.tokenize
import numpy as np

from src.stages.cluster.embeddings.tagger import tag


class Tokenizer:
    def __init__(self, vectors: gensim.models.KeyedVectors):
        self._tokenize = partial(nltk.word_tokenize, language='russian')
        self.vectors = vectors

        self.vectors.add_vector('<unk>', np.zeros(300))
        self.default_index = self.vectors.get_index('<unk>')

    def tokenize(
        self,
        text: str,
        pad: int = None,
        to: Callable = None,
    ):
        tokens = self._tokenize(text)
        tokens = list(map(self.single_tokenize, tokens))

        if pad is not None:
            tokens = tokens[:pad] + [self.default_index] * (pad - len(tokens))

        if to:
            tokens = to(tokens)

        return tokens

    def single_tokenize(self, word):
        return self.vectors.get_index(tag(word), self.default_index)

    def vectorize(self, tokens, to: Callable = None):
        to = to or np.array
        return to(list(map(self.vectors.vectors.__getitem__, tokens)))

    def __call__(
        self,
        text: str,
        pad: int = None,
        to: Callable = None
    ):
        return self.vectorize(self.tokenize(text, pad, to), to)
