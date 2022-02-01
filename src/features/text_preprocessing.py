import re
from functools import partial
from itertools import filterfalse
from typing import List, Set

import nltk
import pymorphy2
import langid


_tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+')
_lemmatizer = nltk.WordNetLemmatizer()
_stemmer = nltk.SnowballStemmer('russian')
_ru_stopwords = nltk.corpus.stopwords.words('russian')
_en_stopwords = nltk.corpus.stopwords.words('english')
_morph = pymorphy2.MorphAnalyzer(lang='ru')
_normal_forms = {}


MAX_SEQ_LENGTH = 3
SEQS = {
    {'jupyter', 'notebook'},

}


def clean_keyseqs(keyseqs: Set[str]) -> Set[str]:
    seqs = set()
    buffer = []

    def release_buffer():
        if buffer:
            seqs.add(' '.join(buffer))
            buffer.clear()

    for seq in keyseqs:
        for word in seq.split():
            if langid.classify(word)[0] == 'en' and not any(partial(set.issubset, {word}), SEQS):
                release_buffer()
                seqs.add(word)
            else:
                buffer.append(word)
        release_buffer()

    return seqs


def remove_numbers(text: str):
    return re.sub(r'\d+', '', text)


def split(text: str):
    text = text.replace('_', '')
    return _tokenizer.tokenize(text)


def remove_stop_words(words: List[str]):
    return list(
        filterfalse(
            _ru_stopwords.__contains__,
            filterfalse(
                _en_stopwords.__contains__,
                words
            )
        )
    )


def lemmatize(words: List[str]):
    return list(map(_lemmatizer.lemmatize, words))


def stem(words: List[str]):
    return list(map(_stemmer.stem, words))


def normalize(word: str):
    if word in _normal_forms:
        return _normal_forms[word]
    return _normal_forms.setdefault(word, _morph.parse(word)[0].normal_form)

