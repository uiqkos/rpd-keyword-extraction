from sklearn.cluster import KMeans

from src.settings import DATA_PATH, MODELS_PATH
from src.utils import file_paths, merge_csv, keywords_from_dataframe

from src.stages.cluster import (
    EmbeddingGrouper,
    RuWikiRuscorporaCBOW_300_10_2021,
    KeywordGroupFactory,
    FrequencyVectorizer,
    Tokenizer
)


def main():
    grouper = EmbeddingGrouper(
        vectorizer=FrequencyVectorizer(
            tokenizer=Tokenizer(
                vectors=RuWikiRuscorporaCBOW_300_10_2021
                    .load(MODELS_PATH / 'embeddings')
            )
        ),
        model=KMeans(**(
            model_params := dict(
                n_clusters=1_000,
                # eps=0.09,
                # min_samples=2,
                # metric='cosine',
                # algorithm='kd_tree'
            )
        )),
        keyword_group_factory=KeywordGroupFactory(
            algorithm='most_common_bigram'
        ),
        save_path=DATA_PATH / 'results' / 'clusters',
        config=dict(
            model=(model_name := 'KMeans'),
            embeddings='weighted sum RuWikiRuscorporaCBOW_300_10_2021',
            **model_params
        ),
        file_name=f'clusters'
                  f'.v1.19'
                  f'.{model_name}'
                  f'.full'
                  f'.emb_ruwiki'
                  f'.json'

    )

    df = merge_csv(file_paths(DATA_PATH / 'raw' / 'data_validation'), columns_take=3)
    keywords = keywords_from_dataframe(df.keywords_processed)

    groups = grouper.apply(keywords)

    print(groups)


if __name__ == '__main__':
    main()
