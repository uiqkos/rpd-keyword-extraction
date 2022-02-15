import json
from dataclasses import dataclass
from operator import attrgetter
from typing import List, Callable, Union

import nltk
from pymorphy2 import MorphAnalyzer

import googletrans


_translator = googletrans.Translator()
_morph_analyzer = MorphAnalyzer(lang='ru')
_stemmer = nltk.SnowballStemmer(language='russian')


@dataclass
class Keyword:
    keyword: str
    words: List[str] = None
    _normal_form: List[str] = None
    _stemmed: List[str] = None
    _translated: str = None
    _lang: str = None  # ru, eng

    @property
    def normal_form(self):
        if self._normal_form is None:
            self._normal_form = [
                _morph_analyzer.parse(word)[0].normal_form
                for word in self.words
            ]
        return self._normal_form

    @property
    def translated(self):
        if self._translated is None:
            translated = _translator.translate(self.keyword)
            self._translated = translated.text
            self._lang = translated.src
            
        return self._translated 
    
    @property
    def lang(self):
        _ = self.translated
        return self._lang
    
    @property
    def stemmed(self):
        if self._stemmed is None:
            self._stemmed = [_stemmer.stem(word) for word in self.words]
        return self._stemmed

    def __hash__(self):
        return hash(self.keyword)

    def __post_init__(self):
        self.words = self.keyword.split()


@dataclass
class KeywordGroup:
    keywords: List[Keyword]

    def to_dict(self):
        return {
            'keywords': list(map(attrgetter('keyword'), self.keywords))
        }


