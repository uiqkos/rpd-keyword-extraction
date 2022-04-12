import pandas as pd
from sklearn.cluster import DBSCAN

from src.stages.cluster.embeddings.embeddinggrouper import EmbeddingGrouper
from src.stages.cluster import RuWikiRuscorporaCBOW_300_10_2021
from src.stages.cluster.keywordgroup import KeywordGroupFactory
from src.stages.cluster.embeddings.vectorizer import FrequencyVectorizer
from src.stages.cluster.embeddings.tokenizer import Tokenizer
from src.stages.converttopdf import ConvertToPdf
from src.stages.download import Download
from src.stages.extracttables import ExtractTables
from src.stages.extractkeywords import ExtractKeywords
from src.pipeline import Pipeline
from src.settings import DATA_PATH, MODELS_PATH

import logging

from src.utils import file_paths

logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)

MARKERS = (
    'Планируемые результаты обучения',
    'Наименование раздела дисциплины',
    'Наименование раздела дисциплины (модуля)',
    'Содержание',

    # ГИА
    'Наименование оценочного средства',
)


def main():
    df = pd.read_csv(DATA_PATH / 'raw' / 'data.csv')
    df = df.head(1)

    pipeline = Pipeline(
        stages=[
            Download(save_path=DATA_PATH / 'documents'),
            ConvertToPdf(),
            ExtractTables(save_path=DATA_PATH / 'tables'),
            ExtractKeywords(markers=MARKERS, flatten_results=True),
            EmbeddingGrouper(
                vectorizer=FrequencyVectorizer(
                    tokenizer=Tokenizer(
                        vectors=RuWikiRuscorporaCBOW_300_10_2021
                            .load(MODELS_PATH / 'embeddings')
                    )
                ),
                model=DBSCAN(
                    eps=0.08,
                    min_samples=2,
                    metric='cosine'
                ),
                keyword_group_factory=KeywordGroupFactory(
                    algorithm='most_common_bigram'
                )
            )
        ],
        generator=False,
        verbose=True
    )

    res = pipeline.apply(*df[['FILE_ID', 'FILE_NAME', 'URL']].values, orient='rows')

    print(res)


if __name__ == '__main__':
    main()
