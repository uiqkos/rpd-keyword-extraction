from functools import reduce
from operator import methodcaller
from typing import List, Callable, Tuple, Dict, Union

from sklearn.cluster import DBSCAN, OPTICS, KMeans
from src.utils import tqdm

from src.stages.cluster.basegrouper import BaseGrouper
from src.stages.cluster.embeddings.vectorizer import Vectorizer
from src.stages.cluster.keywordgroup import KeywordGroup


class EmbeddingGrouper(BaseGrouper):
    def __init__(
        self,
        vectorizer: Vectorizer,
        model: Union[DBSCAN, OPTICS, KMeans],
        keyword_group_factory: Callable[[[str]], KeywordGroup],
        file_name: str = 'clusters.json',
        config: dict = None,
        *args, **kwargs
    ):
        super().__init__(*args, **kwargs, collect_inputs=True)

        self.file_name = file_name
        self.config = config or {}
        self.keyword_to_embedding = vectorizer
        self.model = model
        self.keyword_group_factory = keyword_group_factory

    def apply(self, keywords: List[List[str]]):
        self.keyword_to_embedding.fit(keywords)
        all_keywords = set(reduce(list.__add__, keywords))
        all_keywords.difference_update({'', ' '})

        keyword_by_embedding: Dict[Tuple[float], str] = {}
        X = []

        for keyword in tqdm(all_keywords, desc='Embeddings'):
            embedding = self.keyword_to_embedding(keyword)
            embedding_key = tuple(embedding)
            # todo +0.001 if key in dict
            keyword_by_embedding[embedding_key] = keyword
            X.append(embedding)

        self.model.fit_predict(X)

        group_by_label = {}
        other = []

        for i, label in enumerate(self.model.labels_):
            if label == -1:
                other.append({keyword_by_embedding[tuple(X[i])]})
            else:
                group_by_label.setdefault(label, set()) \
                    .add(keyword_by_embedding[tuple(X[i])])

        groups = list(group_by_label.values()) + other
        groups = list(map(self.keyword_group_factory, groups))

        if self.save:
            self._save_groups(
                list(map(methodcaller('to_dict'), groups)), self.config)

        return groups
