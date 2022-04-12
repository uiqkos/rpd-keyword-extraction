from collections import Counter
from dataclasses import dataclass
from typing import Union, List, Set

from more_itertools import sliding_window
from nltk import word_tokenize


@dataclass
class KeywordGroup:
    center: str
    keywords: Set[str]

    def __iter__(self):
        return iter(self.keywords)

    def to_dict(self):
        return {
            'center': self.center,
            'keywords': list(self.keywords)
        }


class KeywordGroupFactory:
    def __init__(self, algorithm='most_common_word'):
        """
        Создает группу ключевых слов из списка ключевых слов

        Parameters
        ----------
        algorithm: {'most_common_words', 'most_common_word', 'most_common_bigram', 'shortest', 'longest'}
            Алгоритм нахождения центра группы ключевых слов
        """
        self.algorithm = algorithm

    def __call__(self, keywords: Union[Set[str], List[str]]):
        if self.algorithm == 'most_common_words':
            counter = Counter(word_tokenize(' '.join(keywords)))
            center = ', '.join(dict(counter.most_common(2)).keys())

        elif self.algorithm == 'most_common_word':
            counter = Counter(word_tokenize(' '.join(keywords)))
            center = counter.most_common(1)[0][0]

        elif self.algorithm == 'most_common_bigram':
            counter = Counter()

            for keyword in keywords:
                words = word_tokenize(keyword)
                bigrams = list(sliding_window(words, 2)) or (tuple(words),)
                counter += Counter(bigrams)

            center = ' '.join(counter.most_common(1)[0][0])

        elif self.algorithm in ('shortest', 'longest'):
            m = self.algorithm == 'shortest' and min or max
            center = m(keywords, key=len)

        else:
            raise

        return KeywordGroup(center, set(keywords))
