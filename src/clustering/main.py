import json
from functools import reduce, partial
from typing import NewType

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.clustering.keyword import *
from src.clustering.metrics import normal_form_equals, TfIdf, edit_similarity, \
    edit_similarity_transpositions, jaro_similarity_metric, KeywordGroupMetric
from src.settings import DATA_PATH
from src.utils import compose

GroupMetric = NewType('GroupMetric', Callable[[KeywordGroup, KeywordGroup], float])


def run(pool: List[KeywordGroup], metric: GroupMetric, threshold):
    new_pool = []

    for kwg2 in tqdm(pool):
        flag = False
        for i, kwg1 in enumerate(new_pool):
            if metric(kwg1, kwg2) > threshold:
                new_pool[i] = KeywordGroup(kwg1.keywords + kwg2.keywords)
                flag = True
                break

        if not flag:
            new_pool.append(kwg2)

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

    # keywords = keywords.head(100)

    # tf_idf = TfIdf(
    #     docs=keywords,
    #     distance_metric=lambda a, b: np.array_equal(a, b) #compose(cosine, 0.5.__le__)
    # )

    metrics = {
        # 'normal_form_equals': normal_form_equals,
        # 'tf_idf': tf_idf,
        # 'mean edit_similarity': KeywordGroupMetric(edit_similarity, np.mean),
        # 'max edit_similarity': KeywordGroupMetric(edit_similarity, np.max),
        # 'mean edit_similarity_transpositions': KeywordGroupMetric(edit_similarity_transpositions, np.mean),
        'mean jaro_similarity': KeywordGroupMetric(jaro_similarity_metric, np.mean),
    }

    all_keywords = reduce(set.__or__, map(set, keywords))
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
        print('Before:', before := len(pool))
        pool = run(pool, metric, 0.8)
        print('After:', after := len(pool))

        json.dump(
            {'clusters': list(map(KeywordGroup.to_dict, pool)),},
            open(DATA_PATH / 'results' / f'clusters'
                                         f'.{metric_name.replace(" ", "_")}'
                                         f'.small'
                                         f'.{int(100 - 100 * (after / before))}%'
                                         f'.v1.1.json', 'w', encoding='utf-8'),
            ensure_ascii=False,
            indent=4,
        )

        #
        # for kwg in pool:
        #     if len(kwg.keywords) > 1:
        #         print([kw.keyword for kw in kwg.keywords])
