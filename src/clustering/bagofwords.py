import json
from functools import reduce
from operator import attrgetter
from typing import Callable

import numpy as np
from scipy.spatial.distance import cosine
from sklearn.feature_extraction.text import CountVectorizer
from tqdm import tqdm

from src.clustering.main import get_full
from src.settings import DATA_PATH


class Pool:
    def __init__(self, group_comparator: Callable):
        self.group_comparator = group_comparator

    def reduce(self, groups, continue_if_merge=False, verbose=True, reshape=True) -> list[np.array]:
        new_items = []

        if verbose:
            groups = tqdm(groups)

        for group1 in groups:
            if reshape:
                group1 = [group1]

            merged = False

            for i in range(len(new_items)):
                if self.group_comparator(group1, new_items[i]):
                    new_items[i] += group1
                    merged = True
                    if not continue_if_merge:
                        break

            if not merged or continue_if_merge:
                new_items.append(group1)

        return new_items


if __name__ == '__main__':
    limit = 1000
    threshold = 0.9
    preprocess = attrgetter(by := 'normal_form')

    vectorizer = CountVectorizer(stop_words=set())

    _, items = get_full()
    items = items[:limit]
    items = reduce(set.__or__, map(set, items))
    items = list(map(preprocess, items))
    items = vectorizer.fit_transform(items).toarray()
    r, c = items.shape
    items = items.reshape((r, 1, c))

    pool = Pool(lambda l1, l2: (1 - cosine(l1[0], l2[0])) > threshold)

    print('Before:', before := len(items))
    groups = pool.reduce(items)
    print('After:', after := len(groups))
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
                for group in groups
            ]
        },
        open(DATA_PATH / 'results' / fname, 'w', encoding='utf-8'),
        ensure_ascii=False,
        indent=4,
    )

# list[list] 01:52
# list[np.array] 00:27
