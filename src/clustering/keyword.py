from dataclasses import dataclass
from operator import attrgetter
from typing import List, Callable, Union, Iterable

import googletrans
import nltk
from pymorphy2 import MorphAnalyzer

_translator = googletrans.Translator()
_morph_analyzer = MorphAnalyzer(lang='ru')
_stemmer = nltk.SnowballStemmer(language='russian')


@dataclass
class Keyword:
    keyword: str
    words: List[str] = None
    _normal_form: str = None
    _stemmed: str = None
    _translated: str = None
    _lang: str = None  # ru, eng

    @property
    def normal_form(self):
        if self._normal_form is None:
            self._normal_form = ' '.join(
                _morph_analyzer.parse(word)[0].normal_form
                for word in self.words
            )
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
            self._stemmed = ' '.join(_stemmer.stem(word) for word in self.words)
        return self._stemmed

    def __hash__(self):
        return hash(self.keyword)

    def __post_init__(self):
        self.words = self.keyword.split()


def normal_form(w):
    return Keyword(w).normal_form


@dataclass
class KeywordGroup:
    mean: str
    keywords: set

    @classmethod
    def from_keywords(cls, keywords: list, metric: Callable = None):
        metric = metric or (lambda kw: 1 / len(kw))
        return KeywordGroup(max(set(keywords), key=metric), set(keywords))

    def __iter__(self):
        return iter(self.keywords)


@dataclass
class GroupReplacer:
    group: KeywordGroup

    def replace(self, text: Union[str, Iterable]):
        if isinstance(text, str):
            for kw in self.group:
                text = text.replace(kw, self.group.mean)

            return text

        elif isinstance(keywords := text, Iterable):
            for kw in self.group:
                keywords = map(
                    lambda kw:
                        kw
                        if kw not in self.group.keywords
                        else self.group.mean,
                    keywords,
                )

            return list(keywords)

        raise Exception('Error: ' + str(type(text)))
