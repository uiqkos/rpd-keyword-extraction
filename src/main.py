import json
import re
from functools import reduce, partial
from typing import List

import pandas as pd

from src.stages.cluster.keywordgroup import normal_form, KeywordGroup, GroupReplacer

from src.settings import DATA_PATH
from src.utils.merge_csv import merge
from src.utils import file_paths, compose

MARKERS = (
    'Планируемые результаты обучения',
    'Наименование раздела дисциплины',
    'Наименование раздела дисциплины (модуля)',
    'Содержание',

    # ГИА
    'Наименование оценочного средства',
)


def replace(keywords: List[List[str]], groups: List[KeywordGroup]):
    replacers = list(map(GroupReplacer, groups))
    return list(
        map(
            lambda kws: ','.join(set(reduce(
                lambda kws_, replacer: replacer.replace(kws_),
                replacers,
                kws
            ))),
            keywords
        )
    )


def group(threshold, limit, v='1.0', method='bag_of_words', ngram_range=(1, 1)):
    fname = f'clusters' \
            f'.v{v}' \
            f'.size_{limit}' \
            f'.{method}' \
            f'.threshold_{threshold}' \
            f'.json'

    bowgrouper = VecGrouper(
        threshold=threshold,
        preprocessor=compose(lambda w: w.replace('\n', '').strip().lower(), normal_form),
        collect_inputs=True,
        ngram_range=ngram_range,
        save_path=DATA_PATH / 'results' / 'clusters' / fname,
        verbose=True,
    )

    # pipeline = Pipeline([
    #     # Download(save_path=DATA_PATH / 'documents'),
    #     # ConvertToPdf(overwrite=True),
    #     # ExtractTables(unpack_result=True),
    #     # ExtractKeywords(MARKERS, flatten_results=True),
    #     bowgrouper := BagOfWordsGrouper(
    #         threshold=threshold,
    #         preprocessor=compose(lambda w: w.replace('\n', '').strip().lower(), normal_form),
    #         collect_inputs=True,
    #         save_path=DATA_PATH / 'results' / 'clusters' / fname,
    #         verbose=True,
    #     )
    # ], verbose=True)

    # df = merge(file_paths(DATA_PATH / 'raw' / 'data_validation'), columns_take=3)
    df = pd.read_csv(DATA_PATH / 'raw' / 'full_labeled.csv')
    df.drop(df.columns[0], axis=1, inplace=True)
    df = df.head(limit)
    df = df.applymap(lambda s: str(s).replace('\n', ''))

    keywords = (
        df
            .keywords_processed
            .astype(str)
            .map(partial(str.split, sep=','))
    )

    list(map(print, reduce(set.__or__, map(set, keywords))))

    before = sum(map(len, keywords))

    groups = bowgrouper.apply(keywords)
    # with open(DATA_PATH / 'results' / 'clusters' / fname, 'r', encoding='utf-8') as file:
    #     groups = json.load(file)['clusters']

    keyword_groups = list(map(KeywordGroup.from_keywords, groups))
    replacers = list(map(GroupReplacer, keyword_groups))

    docs = df.copy()
    docs['final_keywords'] = list(
        map(
            lambda kws: ','.join(set(reduce(
                lambda kws_, replacer: replacer.replace(kws_),
                replacers,
                kws
            ))),
            keywords
        )
    )
    docs['keywords_processed'] = (
        docs['keywords_processed']
            .astype(str)
            .map(partial(str.split, sep=','))
            .map(lambda kws: ','.join(set(kws)))
    )

    print(docs['final_keywords'])

    docs[docs.columns[1:]].to_csv(DATA_PATH / 'results' / f'replaced.{method}.size_{limit}.v{v}.csv', index=False, )

    # pipeline.apply(items)

    # pipeline = Pipeline((
    #     ExtractKeywords(MARKERS, flatten_results=True, seps=(';', '.')),
    #     PoSTagKeywordFilter(masks=encode_masks(
    #         # ('прил', 'сущ'),
    #         ('сущ', 'сущ', 'сущ'),
    #         ('сущ', 'сущ', 'прил', 'сущ'),
    #         ('нар', 'глаг', 'сущ'),
    #         # ('сущ', 'глаг'),
    #         # ('мест', 'глаг'),
    #     ), str_result=True)
    # ))

    # keywords = pipeline.apply((fs := list(files(DATA_PATH / 'tables'))[:200]))
    #
    # df = pd.DataFrame.from_records(
    #     data=zip(map(attrgetter('name'), fs), keywords),
    #     columns=['filename', 'keywords']
    # )
    # # df['FILE_NAME'] = list(map(attrgetter('name'), fs))
    # df.set_index('filename', drop=True, inplace=True)
    # df.to_csv(DATA_PATH / 'results' / 'pos.small.v1.1.csv')


def count_keywords_deprecated(limit, clusters_filepath) -> 'before, after, %':
    df = pd.read_csv(DATA_PATH / 'raw' / 'full_labeled.csv')
    df.drop(df.columns[0], axis=1, inplace=True)
    df = df.head(limit)
    df = df.applymap(lambda s: str(s).replace('\n', ''))

    unique_keywords = reduce(set.__or__, df.keywords_processed.map(lambda kws: set(kws.split(','))))
    before = len(unique_keywords)

    with open(clusters_filepath, 'r', encoding='utf-8') as file:
        groups = json.load(file)['clusters']

    after = len(groups)

    return before, after, 100 - int((after / before) * 100)


def count_replacements(result_filepath):
    df = pd.read_csv(result_filepath)
    res = 0

    for _, (before, after) in df[['keywords_processed', 'final_keywords']].fillna('').iterrows():
        before = set(before.split(','))
        after = set(after.split(','))
        res += len(before.difference(after))

    return res


def count_unique_keywords(result_filepath):
    df = pd.read_csv(result_filepath)

    before = len(reduce(set.__or__, df.keywords_processed.fillna('').map(lambda kws: set(kws.split(',')))))
    after = len(reduce(set.__or__, df.final_keywords.fillna('').map(lambda kws: set(kws.split(',')))))

    return before, after, 100 - int((after / before) * 100)


def count_keywords(result_filepath):
    df = pd.read_csv(result_filepath)

    before = sum(df.keywords_processed.fillna('').map(lambda kws: len(kws.split(','))))
    after = sum(df.final_keywords.fillna('').map(lambda kws: len(kws.split(','))))

    return before, after, 100 - int((after / before) * 100)


if __name__ == '__main__':


    with open(DATA_PATH / 'results' / 'clusters' / 'clusters.v0.7.size_2344.DBSCAN.json', 'r', encoding='utf-8') as f:
        groups = json.load(f)['clusters']

    df = merge(file_paths(DATA_PATH / 'raw' / 'data_validation'), columns_take=3)

    keywords = (
        df
            .keywords_processed
            .astype(str)
            .map(partial(re.sub, '\n', ''))
            .map(lambda kws: list(filter(lambda l: len(l), kws.split(','))))
    )

    df['replaced'] = replace(keywords, list(map(KeywordGroup.from_keywords, groups)))
    df.to_csv(DATA_PATH / 'results' / f'replaced.v0.2.size_{len(df.replaced)}.csv', index=False)

    for index, (before, after) in df[['keywords_processed', 'replaced']].iterrows():
        if len(before) != len(after):
            print('Before:', ','.join(set(before.split(','))))
            print('After:', ','.join(set(after.split(','))))

    # print(count_keywords(
    #     1000, DATA_PATH / 'results' / 'clusters' / 'clusters.v1.0.size_1000.bag_of_words.threshold_0.75.json'))
    # group(0.75, 1000, v='0.1', method='n-gram(2, 3)', ngram_range=(2, 3))
    # print(count_replacements(DATA_PATH / 'results' / f'replaced.n-gram(1, 2).size_1000.v0.1.csv')) # 1160
    # print('Unique:', count_unique_keywords(DATA_PATH / 'results' / f'replaced.n-gram(1, 2).size_1000.v0.1.csv'))
    # print('All:', count_keywords(DATA_PATH / 'results' / f'replaced.n-gram(1, 2).size_1000.v0.1.csv'))
