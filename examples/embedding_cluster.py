import json
from collections import Counter
from functools import reduce
from typing import Tuple, Dict, Union

import numpy as np
from more_itertools import minmax
from nltk import word_tokenize
from sklearn.cluster import DBSCAN, OPTICS
from src.utils import tqdm

from src.stages.cluster import RuWikiRuscorporaCBOW_300_10_2021
from src.stages.cluster.keywordgroup import KeywordGroup
from src.stages.cluster.embeddings.tokenizer import Tokenizer
from src.settings import DATA_PATH, MODELS_PATH
from src.utils import file_paths, merge_csv, keywords_from_dataframe


def cluster(keywords, model: Union[DBSCAN, OPTICS]):
    all_keywords = set(reduce(list.__add__, keywords))
    all_keywords.difference_update({'', ' '})

    tokenizer = Tokenizer(
        RuWikiRuscorporaCBOW_300_10_2021
            .load(MODELS_PATH / 'embeddings')
    )

    word_counter = Counter(
        reduce(
            list.__add__,
            map(tokenizer.tokenize, all_keywords)
        )
    )

    mn, mx = minmax(word_counter.values())

    def normalize(x):
        return np.array([(x_ - mn) / (mx - mn) for x_ in x])

    def keyword_to_embedding(keyword: str):
        indexes = tokenizer.tokenize(keyword)
        counts = list(map(word_counter.get, indexes))  # n x 1
        vec = 1 - normalize(counts)
        embeddings = tokenizer.vectorize(indexes, to=np.array)  # n x 300

        return embeddings.T @ vec  # 300 x 1

    keyword_by_embedding: Dict[Tuple[float], str] = {}
    X = []

    for keyword in tqdm(all_keywords, desc='Embeddings'):
        embedding = keyword_to_embedding(keyword)
        embedding_key = tuple(embedding)
        # todo +0.001 if key in dict
        keyword_by_embedding[embedding_key] = keyword
        X.append(embedding)

    model.fit_predict(X)

    groups = {}
    other = []

    for i, label in enumerate(model.labels_):
        if label == -1:
            other.append({keyword_by_embedding[tuple(X[i])]})
        else:
            groups.setdefault(label, set()) \
                .add(keyword_by_embedding[tuple(X[i])])

    return list(groups.values()) + other


def main():
    model_params = dict(
        eps=0.08,
        min_samples=2,
        metric='cosine'
    )
    params = dict(
        v='1.8.6',
        group_fn='weighted sum',
        model='DBSCAN',
        model_params=model_params
    )

    v = '1.9'
    limit = -1
    model_name = 'DBSCAN'
    model = DBSCAN(**model_params)

    path = DATA_PATH / 'raw' / 'data_validation'
    df = merge_csv(file_paths(path), columns_take=3)
    df = df.head(limit)

    keywords = keywords_from_dataframe(df.keywords_processed)

    groups = cluster(keywords, model)

    def most_common_group_center(kws) -> str:
        return ', '.join(dict(Counter(word_tokenize(' '.join(kws))).most_common(2)).keys())

    keyword_groups = [
        KeywordGroup(most_common_group_center(kws), kws)
        for kws in groups
    ]

    file_name = f'clusters' \
            f'.v{v}' \
            f'.size_{len(df)}' \
            f'.{model_name}' \
            f'.json'

    with open(DATA_PATH / 'results' / 'clusters' / file_name, 'w', encoding='utf-8') as f:
        json.dump({
            'params': params,
            'clusters': [
                {
                    'mean': g.center,
                    'keywords': list(g.keywords)
                } for g in keyword_groups
            ]
        }, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()
