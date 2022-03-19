import re
from functools import partial
from operator import attrgetter, itemgetter
from typing import List, Iterable

import pymorphy2
import spacy

from src.morphy_utils import matches_mask
from src.stages import Stage
from src.utils import identity, compose, progressbar


class PoSTagKeywordFilter(Stage):
    def __init__(self, masks: Iterable[tuple], str_result=False, flatten_results=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.masks = masks
        self.flatten_results = flatten_results
        self.str_result = str_result

    def apply_generator(self, docs_keywords: Iterable[Iterable[str]]):
        combine_words = ' '.join if self.str_result else tuple
        combine_keywords = ','.join if self.str_result else tuple

        for keywords in progressbar(docs_keywords):
            filtered = set()
            for keyword in keywords:
                doc = list(map(itemgetter(0), map(morph_analyzer.parse, re.findall(r'\w+', keyword))))

                for mask in self.masks:
                    filtered.update(set(map(combine_words, map(partial(map, attrgetter('word')), filter(
                        partial(matches_mask, mask=mask, key=compose(
                            attrgetter('tag'), attrgetter('POS'))),
                        map(
                            lambda start: doc[start:start + len(mask)],
                            range(len(doc) - len(mask) + 1)
                        )
                    )))))

            if self.flatten_results:
                for kw in filtered:
                    yield kw
            else:
                yield combine_keywords(filtered)

    def apply(self, *args, **kwargs):
        return list(self.apply_generator(*args, **kwargs))
