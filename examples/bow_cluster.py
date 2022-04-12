import numpy as np
from nltk import word_tokenize
from scipy.spatial.distance import cosine

from src.settings import DATA_PATH
from src.stages.cluster import Grouper, PoolFactory
from src.stages.cluster.metrics import ComparatorFromDistanceMetric, BagOfWordsDistance, GroupMetric
from src.utils import file_paths, merge_csv, keywords_from_dataframe


def main():
    grouper = Grouper(
        pool_factory=PoolFactory(
            group_comparator=GroupMetric(
                single_metric=ComparatorFromDistanceMetric(
                    BagOfWordsDistance(
                        distance_metric=cosine,
                        preprocessor=lambda s: ' '.join(word_tokenize(s, 'russian')),
                    ),
                    threshold=(threshold := 0.75)
                ),
                group_metric=np.mean
            )
        ),
        save_path=DATA_PATH / 'results' / 'clusters',
        file_name=f'clusters'
                  f'.v1.19'
                  f'.threshold_{threshold}'
                  f'.full'
                  f'.json',
        verbose=True,
    )

    df = merge_csv(file_paths(DATA_PATH / 'raw' / 'data_validation'), columns_take=3)
    df = df.head(100)
    keywords = keywords_from_dataframe(df.keywords_processed)

    groups = grouper.apply(keywords)

    print(groups)


if __name__ == '__main__':
    main()
