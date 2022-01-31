import re
from itertools import filterfalse
from typing import List

import nltk
import pymorphy2


_tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+')
_lemmatizer = nltk.WordNetLemmatizer()
_stemmer = nltk.SnowballStemmer('russian')
_ru_stopwords = nltk.corpus.stopwords.words('russian')
_en_stopwords = nltk.corpus.stopwords.words('english')
_morph = pymorphy2.MorphAnalyzer(lang='ru')
_normal_forms = {}

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

