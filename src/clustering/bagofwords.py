import json
from functools import reduce, partial
from operator import attrgetter
from pprint import pprint
from typing import Callable, List

import numpy as np
from scipy.spatial.distance import cosine
from sklearn.feature_extraction.text import CountVectorizer
from tqdm import tqdm

from src.clustering.main import get_full
from src.clustering.metrics import BagOfWordsSimilarity, _keyword_to_string_stemmed
from src.settings import DATA_PATH
from src.utils import compose


class Pool:
    def __init__(self,
                 group_comparator: Callable[[list, list], bool],
                 groups: list[list]):
        self.groups = np.array(groups)  # если разных рамеров мб дед
        self.group_comparator = group_comparator

    def reduce(self) -> int:
        new_items = []
        prev_len = len(self.groups)

        for group1 in tqdm(self.groups):
            merged = False
            for i, group2 in enumerate(new_items):
                if self.group_comparator(group1, group2):
                    new_items[i] = np.concatenate([new_items[i], group1])
                    merged = True
                    break

            if not merged:
                new_items.append(group1)

        self.groups = new_items

        return len(self.groups) - prev_len

    def __len__(self) -> int:
        return len(self.groups)


if __name__ == '__main__':
    limit = 1000
    threshold = 0.8
    preprocess = attrgetter(by := 'normal_form')

    vectorizer = CountVectorizer(stop_words=set())

    _, items = get_full()
    items = items[:limit]
    items = reduce(set.__or__, map(set, items))
    items = list(map(preprocess, items))
    items = vectorizer.fit_transform(items).toarray()
    r, c = items.shape
    items = items.reshape((r, 1, c))

    pool = Pool(lambda l1, l2: (1 - cosine(l1[0], l2[0])) > threshold, items)

    print('Before:', before := len(pool))
    pool.reduce()
    print('After:', after := len(pool))
    pc = int(100 - 100 * (after / before))
    print(f'-------------  {pc}%  -------------')

    fname = f'clusters' \
            f'.bag_of_words' \
            f'.{by}' \
            f'.threshold_{threshold}' \
            f'.small' \
            f'.{pc}%' \
            f'.v2.1.json'

    json.dump(
        {
            'clusters': [
                list(map(' '.join, vectorizer.inverse_transform(group)))
                for group in pool.groups
            ]
        },
        open(DATA_PATH / 'results' / fname, 'w', encoding='utf-8'),
        ensure_ascii=False,
        indent=4,
    )

# list[list] 01:52
# list[np.array] 00:27
