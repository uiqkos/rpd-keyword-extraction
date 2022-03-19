import json
from functools import reduce, partial
from typing import NewType, Callable

import numpy as np
import pandas as pd
from scipy.spatial.distance import cosine
from tqdm import tqdm

from src.clustering.keyword import *
from src.clustering.metrics import _keyword_to_string_stemmed, KeywordGroupSingleMetric
from src.settings import DATA_PATH
from src.utils.utils import compose

GroupMetric = NewType('GroupMetric', Callable[[KeywordGroup, KeywordGroup], float])


def run(pool: List[KeywordGroup], metric: GroupMetric, threshold):
    new_pool = []
    # counter = tnrange(len(pool), desc='Group count', unit=' groups')

    for kwg2 in tqdm(pool):
        flag = False
        for i, kwg1 in enumerate(new_pool):
            if metric(kwg1, kwg2) > threshold:
                new_pool[i] = KeywordGroup(kwg1.keywords + kwg2.keywords)
                flag = True
                # counter.update()
                break

        if not flag:
            new_pool.append(kwg2)
            # counter.update()

    return new_pool


def get_full():
    df = pd.read_csv(DATA_PATH / 'results' / 'keybert.full.v1.1.csv')
    df.set_index('filename', inplace=True)
    keywords = df.keywords.apply(compose(
        str, partial(str.split, sep=','),
        partial(map, Keyword), list
    ))
    return df, keywords


def get_pos():
    df = pd.read_csv(DATA_PATH / 'results' / 'keybert.small.v2.5.csv')
    df.set_index('filename', inplace=True)
    keywords = df.all_keywords.apply(compose(
        str, partial(str.split, sep=','),
        partial(map, Keyword), list
    ))
    return df, keywords


if __name__ == '__main__':
    df, keywords = get_full()

    keywords = keywords.head(100)
    all_keywords = reduce(set.__or__, map(set, keywords))

    # tf_idf = TfIdf(
    #     docs=keywords,
    #     distance_metric=lambda a, b: np.array_equal(a, b) compose(cosine, 0.5.__le__)
    # )

    metrics = {
        # 'normal_form_equals': normal_form_equals,
        # 'tf_idf': tf_idf,
        # 'mean edit_similarity': GroupMetric(edit_similarity, np.mean),
        # 'max edit_similarity': GroupMetric(edit_similarity, np.max),
        # 'mean edit_similarity_transpositions': GroupMetric(edit_similarity_transpositions, np.mean),
        # 'mean jaro_similarity': GroupMetric(jaro_similarity_metric, np.mean),
        'mean bag of words': KeywordGroupSingleMetric(
            keyword_metric=BagOfWordsSimilarity(
                distance_metric=cosine,
                docs=list(all_keywords),
                kw_to_str=_keyword_to_string_stemmed
            ),
            group_metric=np.mean
        ),
        # 'normal_form_equals': GroupMetric(normal_form_equals, np.max)
    }

    #
    # c = Counter(map(attrgetter('keyword'), all_keywords))

    # print(c.most_common(10))
    # print(c['uml'])
    # print(c['idef'])

    # ckw = 'понимать эксплицитно выраженное отношение автора'
    # count = 0
    #
    # for idx, doc in zip(keywords.index, keywords):
    #     if ckw in (s := list(map(attrgetter('keyword'), doc))):
    #         count += 1
    #         print(idx, s)
    #
    # print(count)

    # print(tf_idf_._vectorizer.fit_transform(['программного обеспечения']))

    for metric_name, metric in metrics.items():
        pool = list(map(lambda kw: KeywordGroup([kw]), all_keywords))
        print(metric_name)
        before = len(pool)
        pool = run(pool, metric, 0.9)
        print('Before:', before)
        print('After:', after := len(pool))
        print('Result:', pc := int(100 - 100 * (after / before)))

        json.dump(
            {'clusters': list(map(KeywordGroup.to_dict, pool)), },
            open(DATA_PATH / 'results' / f'clusters'
                                         f'.{metric_name.replace(" ", "_")}'
                                         f'.small'
                                         f'.{pc}%'
                                         f'.v1.1.json', 'w', encoding='utf-8'),
            ensure_ascii=False,
            indent=4,
        )

        for kwg in pool:
            if len(kwg.keywords) > 1:
                print([kw.keyword for kw in kwg.keywords])
